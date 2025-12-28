"""
Billing and subscription management routes.

Provides endpoints for:
- Viewing current plan and usage
- Creating Stripe checkout sessions
- Managing subscriptions via customer portal
"""

from quart import Blueprint, jsonify, request
from app.utils.auth_utils import requires_auth
from app.utils.plan_utils import get_plan_limits
from app.database import SessionLocal
from app.models import Tenant, TenantUsage
from app.config import (
    STRIPE_SECRET_KEY,
    STRIPE_PRICE_STARTER,
    STRIPE_PRICE_BUSINESS,
    STRIPE_PRICE_ENTERPRISE
)
from datetime import datetime
import stripe

stripe.api_key = STRIPE_SECRET_KEY

billing_bp = Blueprint('billing', __name__)


@billing_bp.route('/api/billing/usage', methods=['GET'])
@requires_auth()
async def get_usage():
    """
    Get current usage and limits for the authenticated user's tenant.

    Returns:
        {
            "tenant_id": 999,
            "plan_tier": "starter",
            "status": "active",
            "usage": {
                "storage_bytes": 1024000,
                "storage_mb": 1.0,
                "db_record_count": 50,
                "api_calls_today": 100,
                "emails_this_month": 5
            },
            "limits": {
                "max_users": 3,
                "max_storage_bytes": 2147483648,
                "max_storage_gb": 2.0,
                "max_db_records": 5000,
                "max_api_calls_per_day": 5000,
                "max_emails_per_month": 100,
                "features": {}
            },
            "percentage_used": {
                "storage": 0.05,
                "records": 1.0,
                "api_calls": 2.0,
                "emails": 5.0
            },
            "reset_times": {
                "api_calls_reset_at": "2025-12-29T14:41:00Z",
                "emails_reset_at": "2026-01-01T00:00:00Z"
            }
        }
    """
    user = request.user
    tenant_id = user.tenant_id

    session = SessionLocal()
    try:
        # Get tenant info
        tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404

        # Get usage
        usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
        if not usage:
            return jsonify({"error": "Usage data not found"}), 404

        # Get limits
        limits = get_plan_limits(tenant.plan_tier, session)

        # Calculate percentage used
        percentage_used = {}

        # Storage percentage
        if limits['max_storage_bytes'] > 0:
            percentage_used['storage'] = round(
                (usage.storage_bytes / limits['max_storage_bytes']) * 100, 2
            )
        else:
            percentage_used['storage'] = 0 if usage.storage_bytes == 0 else 100

        # Records percentage
        if limits['max_db_records'] > 0:
            percentage_used['records'] = round(
                (usage.db_record_count / limits['max_db_records']) * 100, 2
            )
        else:
            percentage_used['records'] = 0

        # API calls percentage
        if limits['max_api_calls_per_day'] > 0:
            percentage_used['api_calls'] = round(
                (usage.api_calls_today / limits['max_api_calls_per_day']) * 100, 2
            )
        else:
            percentage_used['api_calls'] = 0

        # Emails percentage
        if limits['max_emails_per_month'] > 0:
            percentage_used['emails'] = round(
                (usage.emails_this_month / limits['max_emails_per_month']) * 100, 2
            )
        else:
            percentage_used['emails'] = 0

        return jsonify({
            "tenant_id": tenant_id,
            "plan_tier": tenant.plan_tier,
            "status": tenant.status.value,
            "usage": {
                "storage_bytes": usage.storage_bytes,
                "storage_mb": round(usage.storage_bytes / (1024 * 1024), 2),
                "storage_gb": round(usage.storage_bytes / (1024 * 1024 * 1024), 2),
                "db_record_count": usage.db_record_count,
                "api_calls_today": usage.api_calls_today,
                "emails_this_month": usage.emails_this_month
            },
            "limits": {
                "max_users": limits['max_users'],
                "max_storage_bytes": limits['max_storage_bytes'],
                "max_storage_mb": round(limits['max_storage_bytes'] / (1024 * 1024), 2),
                "max_storage_gb": round(limits['max_storage_bytes'] / (1024 * 1024 * 1024), 2),
                "max_db_records": limits['max_db_records'],
                "max_api_calls_per_day": limits['max_api_calls_per_day'],
                "max_emails_per_month": limits['max_emails_per_month'],
                "features": limits.get('features', {})
            },
            "percentage_used": percentage_used,
            "reset_times": {
                "api_calls_reset_at": usage.api_calls_reset_at.isoformat() if usage.api_calls_reset_at else None,
                "emails_reset_at": usage.emails_reset_at.isoformat() if usage.emails_reset_at else None
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@billing_bp.route('/api/billing/plan', methods=['GET'])
@requires_auth()
async def get_plan():
    """
    Get current plan details for the authenticated user's tenant.

    Returns:
        {
            "plan_tier": "starter",
            "status": "active",
            "billing_email": "test@example.com",
            "company_name": "Test Company",
            "stripe_customer_id": null,
            "current_period_start": null,
            "current_period_end": null
        }
    """
    user = request.user
    tenant_id = user.tenant_id

    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404

        return jsonify({
            "plan_tier": tenant.plan_tier,
            "status": tenant.status.value,
            "billing_email": tenant.billing_email,
            "company_name": tenant.company_name,
            "stripe_customer_id": tenant.stripe_customer_id,
            "current_period_start": tenant.current_period_start.isoformat() if tenant.current_period_start else None,
            "current_period_end": tenant.current_period_end.isoformat() if tenant.current_period_end else None
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@billing_bp.route('/api/billing/create-checkout-session', methods=['POST'])
@requires_auth()
async def create_checkout_session():
    """
    Create a Stripe checkout session for plan upgrade/subscription.

    Request body:
        {
            "plan_tier": "starter" | "business" | "enterprise",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        }

    Returns:
        {
            "checkout_url": "https://checkout.stripe.com/..."
        }
    """
    user = request.user
    tenant_id = user.tenant_id
    data = await request.get_json()

    plan_tier = data.get('plan_tier')
    success_url = data.get('success_url', 'http://localhost:3000/billing/success')
    cancel_url = data.get('cancel_url', 'http://localhost:3000/billing')

    # Validate plan tier
    if plan_tier not in ['starter', 'business', 'enterprise']:
        return jsonify({"error": "Invalid plan tier"}), 400

    # Map plan to Stripe price ID
    price_map = {
        'starter': STRIPE_PRICE_STARTER,
        'business': STRIPE_PRICE_BUSINESS,
        'enterprise': STRIPE_PRICE_ENTERPRISE
    }

    price_id = price_map[plan_tier]
    if not price_id:
        return jsonify({"error": f"Stripe price ID not configured for {plan_tier} plan"}), 500

    session_db = SessionLocal()
    try:
        tenant = session_db.query(Tenant).filter_by(id=tenant_id).first()
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404

        # Create or retrieve Stripe customer
        if tenant.stripe_customer_id:
            customer_id = tenant.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=tenant.billing_email or user.email,
                metadata={
                    'tenant_id': tenant_id,
                    'company_name': tenant.company_name or ''
                }
            )
            customer_id = customer.id
            tenant.stripe_customer_id = customer_id
            session_db.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'tenant_id': tenant_id,
                'plan_tier': plan_tier
            }
        )

        return jsonify({
            "checkout_url": checkout_session.url
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": f"Stripe error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session_db.close()


@billing_bp.route('/api/billing/customer-portal', methods=['POST'])
@requires_auth()
async def create_customer_portal_session():
    """
    Create a Stripe customer portal session for managing subscription.

    Request body:
        {
            "return_url": "https://example.com/billing"
        }

    Returns:
        {
            "portal_url": "https://billing.stripe.com/..."
        }
    """
    user = request.user
    tenant_id = user.tenant_id
    data = await request.get_json()

    return_url = data.get('return_url', 'http://localhost:3000/billing')

    session_db = SessionLocal()
    try:
        tenant = session_db.query(Tenant).filter_by(id=tenant_id).first()
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 404

        if not tenant.stripe_customer_id:
            return jsonify({"error": "No active subscription found"}), 404

        # Create customer portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=tenant.stripe_customer_id,
            return_url=return_url
        )

        return jsonify({
            "portal_url": portal_session.url
        }), 200

    except stripe.error.StripeError as e:
        return jsonify({"error": f"Stripe error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session_db.close()
