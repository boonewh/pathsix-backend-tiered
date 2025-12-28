"""
Stripe webhook handlers.

Handles Stripe events for subscription lifecycle:
- checkout.session.completed: New subscription created
- customer.subscription.updated: Subscription changed
- customer.subscription.deleted: Subscription cancelled
- invoice.payment_succeeded: Payment successful
- invoice.payment_failed: Payment failed
"""

from quart import Blueprint, request, jsonify
from app.database import SessionLocal
from app.models import Tenant, Subscription, TenantStatus, SubscriptionStatus
from app.config import STRIPE_WEBHOOK_SECRET
from datetime import datetime
import stripe
import logging

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/api/webhooks/stripe', methods=['POST'])
async def stripe_webhook():
    """
    Handle Stripe webhook events.

    Verifies webhook signature and processes subscription events.
    """
    payload = await request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        return jsonify({"error": "Invalid signature"}), 400

    # Handle the event
    event_type = event['type']
    data_object = event['data']['object']

    session_db = SessionLocal()
    try:
        if event_type == 'checkout.session.completed':
            await handle_checkout_completed(data_object, session_db)

        elif event_type == 'customer.subscription.updated':
            await handle_subscription_updated(data_object, session_db)

        elif event_type == 'customer.subscription.deleted':
            await handle_subscription_deleted(data_object, session_db)

        elif event_type == 'invoice.payment_succeeded':
            await handle_payment_succeeded(data_object, session_db)

        elif event_type == 'invoice.payment_failed':
            await handle_payment_failed(data_object, session_db)

        else:
            logger.info(f"Unhandled event type: {event_type}")

        session_db.commit()
        return jsonify({"status": "success"}), 200

    except Exception as e:
        session_db.rollback()
        logger.error(f"Error processing webhook: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        session_db.close()


async def handle_checkout_completed(session_obj, db_session):
    """Handle successful checkout session completion."""
    customer_id = session_obj.get('customer')
    subscription_id = session_obj.get('subscription')
    metadata = session_obj.get('metadata', {})
    tenant_id = metadata.get('tenant_id')
    plan_tier = metadata.get('plan_tier')

    if not tenant_id:
        logger.error("No tenant_id in checkout session metadata")
        return

    tenant = db_session.query(Tenant).filter_by(id=int(tenant_id)).first()
    if not tenant:
        logger.error(f"Tenant {tenant_id} not found")
        return

    # Update tenant with subscription info
    tenant.stripe_customer_id = customer_id
    tenant.stripe_subscription_id = subscription_id
    tenant.plan_tier = plan_tier
    tenant.status = TenantStatus.active

    # Retrieve full subscription object from Stripe
    subscription = stripe.Subscription.retrieve(subscription_id)
    tenant.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
    tenant.current_period_end = datetime.fromtimestamp(subscription.current_period_end)

    # Create subscription record
    sub_record = Subscription(
        tenant_id=int(tenant_id),
        stripe_subscription_id=subscription_id,
        stripe_customer_id=customer_id,
        plan_tier=plan_tier,
        status=SubscriptionStatus.active,
        current_period_start=tenant.current_period_start,
        current_period_end=tenant.current_period_end
    )
    db_session.add(sub_record)

    logger.info(f"Checkout completed for tenant {tenant_id}, plan: {plan_tier}")


async def handle_subscription_updated(subscription_obj, db_session):
    """Handle subscription updates (plan changes, renewals)."""
    subscription_id = subscription_obj['id']
    customer_id = subscription_obj['customer']
    status = subscription_obj['status']

    tenant = db_session.query(Tenant).filter_by(stripe_subscription_id=subscription_id).first()
    if not tenant:
        logger.error(f"Tenant not found for subscription {subscription_id}")
        return

    # Update tenant status based on subscription status
    status_map = {
        'active': TenantStatus.active,
        'past_due': TenantStatus.suspended,
        'canceled': TenantStatus.cancelled,
        'unpaid': TenantStatus.suspended
    }

    tenant.status = status_map.get(status, TenantStatus.active)
    tenant.current_period_start = datetime.fromtimestamp(subscription_obj['current_period_start'])
    tenant.current_period_end = datetime.fromtimestamp(subscription_obj['current_period_end'])

    # Update subscription record
    sub_record = db_session.query(Subscription).filter_by(
        stripe_subscription_id=subscription_id
    ).first()

    if sub_record:
        sub_record.status = SubscriptionStatus[status]
        sub_record.current_period_start = tenant.current_period_start
        sub_record.current_period_end = tenant.current_period_end

    logger.info(f"Subscription updated for tenant {tenant.id}, status: {status}")


async def handle_subscription_deleted(subscription_obj, db_session):
    """Handle subscription cancellation."""
    subscription_id = subscription_obj['id']

    tenant = db_session.query(Tenant).filter_by(stripe_subscription_id=subscription_id).first()
    if not tenant:
        logger.error(f"Tenant not found for subscription {subscription_id}")
        return

    # Downgrade to free tier
    tenant.plan_tier = 'free'
    tenant.status = TenantStatus.cancelled
    tenant.stripe_subscription_id = None

    # Update subscription record
    sub_record = db_session.query(Subscription).filter_by(
        stripe_subscription_id=subscription_id
    ).first()

    if sub_record:
        sub_record.status = SubscriptionStatus.canceled
        sub_record.cancelled_at = datetime.utcnow()

    logger.info(f"Subscription deleted for tenant {tenant.id}, downgraded to free")


async def handle_payment_succeeded(invoice_obj, db_session):
    """Handle successful payment."""
    subscription_id = invoice_obj.get('subscription')
    if not subscription_id:
        return

    tenant = db_session.query(Tenant).filter_by(stripe_subscription_id=subscription_id).first()
    if not tenant:
        return

    # Ensure tenant is active
    tenant.status = TenantStatus.active

    logger.info(f"Payment succeeded for tenant {tenant.id}")


async def handle_payment_failed(invoice_obj, db_session):
    """Handle failed payment."""
    subscription_id = invoice_obj.get('subscription')
    if not subscription_id:
        return

    tenant = db_session.query(Tenant).filter_by(stripe_subscription_id=subscription_id).first()
    if not tenant:
        return

    # Suspend tenant on payment failure
    tenant.status = TenantStatus.suspended

    # Update subscription status
    sub_record = db_session.query(Subscription).filter_by(
        stripe_subscription_id=subscription_id
    ).first()

    if sub_record:
        sub_record.status = SubscriptionStatus.past_due

    logger.warning(f"Payment failed for tenant {tenant.id}, status set to suspended")
