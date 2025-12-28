"""
Quota enforcement middleware for tiered pricing.

This middleware runs BEFORE request handlers to check if tenant has exceeded quotas.
For read-only mode, it blocks POST/PUT/DELETE but allows GET.
"""

from functools import wraps
from quart import request, jsonify
from app.database import SessionLocal
from app.models import Tenant, TenantUsage, TenantStatus
from datetime import datetime, timedelta
from app.utils.plan_utils import get_plan_limits
from app.middleware.usage_tracker import usage_tracker


def _evaluate_tenant_status(tenant: Tenant, method: str):
    """Return an error response if the tenant's status blocks the request."""
    if tenant.status == TenantStatus.suspended:
        return jsonify({
            "error": "Account suspended",
            "message": "Your account has been suspended due to payment issues. Please update your billing information.",
            "upgrade_url": "/billing/update"
        }), 403

    if tenant.status == TenantStatus.cancelled:
        return jsonify({
            "error": "Account cancelled",
            "message": "This account has been cancelled."
        }), 403

    if tenant.status == TenantStatus.read_only and method in ["POST", "PUT", "DELETE", "PATCH"]:
        return jsonify({
            "error": "Quota exceeded",
            "message": "Your account has exceeded quota limits and is in read-only mode. Please upgrade your plan.",
            "status": "read_only",
            "upgrade_url": "/billing/upgrade"
        }), 403

    return None


def _ensure_usage_record(session, tenant_id: int) -> TenantUsage:
    """
    Ensure a TenantUsage row exists and has reset windows populated.
    """
    from dateutil.relativedelta import relativedelta

    usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
    created_or_updated = False

    if not usage:
        usage = TenantUsage(
            tenant_id=tenant_id,
            api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
            emails_reset_at=(datetime.utcnow() + relativedelta(months=1)).replace(day=1)
        )
        session.add(usage)
        created_or_updated = True

    if usage.api_calls_reset_at is None:
        usage.api_calls_reset_at = datetime.utcnow() + timedelta(days=1)
        created_or_updated = True

    if usage.emails_reset_at is None:
        usage.emails_reset_at = (datetime.utcnow() + relativedelta(months=1)).replace(day=1)
        created_or_updated = True

    if created_or_updated:
        session.commit()

    return usage


def _reset_usage_windows(usage: TenantUsage, session):
    """Reset daily/monthly counters when their windows have expired."""
    from dateutil.relativedelta import relativedelta

    now = datetime.utcnow()
    updated = False

    if usage.api_calls_reset_at and now > usage.api_calls_reset_at:
        usage.api_calls_today = 0
        usage.api_calls_reset_at = now + timedelta(days=1)
        updated = True

    if usage.emails_reset_at and now > usage.emails_reset_at:
        usage.emails_this_month = 0
        usage.emails_reset_at = (now + relativedelta(months=1)).replace(day=1)
        updated = True

    if updated:
        session.commit()


def requires_quota(quota_type: str = None):
    """
    Decorator to enforce quota limits on endpoints.

    Args:
        quota_type: Type of quota to check ('storage', 'records', 'api', 'emails')
                   If None, checks tenant status only

    Usage:
        @requires_quota('records')
        async def create_client():
            ...

    Returns:
        403 with detailed error message if quota exceeded
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            # Skip for OPTIONS requests (CORS)
            if request.method == "OPTIONS":
                return await fn(*args, **kwargs)

            user = getattr(request, 'user', None)
            if not user:
                # No user attached = no auth required = no quota check
                return await fn(*args, **kwargs)

            session = SessionLocal()
            try:
                # Get tenant and usage
                tenant = session.query(Tenant).filter_by(id=user.tenant_id).first()
                if not tenant:
                    return jsonify({"error": "Tenant not found"}), 500

                status_response = _evaluate_tenant_status(tenant, request.method)
                if status_response:
                    return status_response

                usage = _ensure_usage_record(session, user.tenant_id)
                _reset_usage_windows(usage, session)

                # Get plan limits
                limits = get_plan_limits(tenant.plan_tier, session)

                # Check specific quota type if provided
                if quota_type == 'records':
                    if limits['max_db_records'] != -1 and usage.db_record_count >= limits['max_db_records']:
                        return jsonify({
                            "error": "Record limit exceeded",
                            "message": f"You've reached the maximum of {limits['max_db_records']:,} records for your {tenant.plan_tier} plan.",
                            "current_usage": usage.db_record_count,
                            "limit": limits['max_db_records'],
                            "plan_tier": tenant.plan_tier,
                            "upgrade_url": "/billing/upgrade"
                        }), 403

                elif quota_type == 'storage':
                    if limits['max_storage_bytes'] != -1 and usage.storage_bytes >= limits['max_storage_bytes']:
                        return jsonify({
                            "error": "Storage limit exceeded",
                            "message": f"You've reached your storage limit for the {tenant.plan_tier} plan.",
                            "current_usage_gb": round(usage.storage_bytes / (1024**3), 2),
                            "limit_gb": round(limits['max_storage_bytes'] / (1024**3), 2),
                            "plan_tier": tenant.plan_tier,
                            "upgrade_url": "/billing/upgrade"
                        }), 403

                elif quota_type == 'emails':
                    if usage.emails_this_month >= limits['max_emails_per_month']:
                        return jsonify({
                            "error": "Email limit exceeded",
                            "message": f"You've reached your email limit of {limits['max_emails_per_month']:,} for this month.",
                            "current_usage": usage.emails_this_month,
                            "limit": limits['max_emails_per_month'],
                            "reset_date": usage.emails_reset_at.isoformat(),
                            "plan_tier": tenant.plan_tier,
                            "upgrade_url": "/billing/upgrade"
                        }), 403

                # Proceed with request
                return await fn(*args, **kwargs)

            finally:
                session.close()

        return wrapper
    return decorator


def requires_plan(tiers: list):
    """
    Decorator to restrict endpoints to specific plan tiers.

    Args:
        tiers: List of allowed tiers (e.g., ['starter', 'business', 'enterprise'])

    Usage:
        @requires_plan(['business', 'enterprise'])
        async def advanced_feature():
            ...

    Returns:
        403 if tenant's plan is not in the allowed tiers
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            user = getattr(request, 'user', None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401

            session = SessionLocal()
            try:
                tenant = session.query(Tenant).filter_by(id=user.tenant_id).first()
                if not tenant:
                    return jsonify({"error": "Tenant not found"}), 500

                if tenant.plan_tier not in tiers:
                    # Find the lowest tier that has access
                    tier_order = ['free', 'starter', 'business', 'enterprise']
                    required_tier = None
                    for tier in tier_order:
                        if tier in tiers:
                            required_tier = tier
                            break

                    return jsonify({
                        "error": "Plan upgrade required",
                        "message": f"This feature requires the {required_tier} plan or higher.",
                        "current_plan": tenant.plan_tier,
                        "required_plan": required_tier,
                        "upgrade_url": "/billing/upgrade"
                    }), 403

                return await fn(*args, **kwargs)

            finally:
                session.close()

        return wrapper
    return decorator


async def enforce_api_quota(user) -> tuple | None:
    """
    Check tenant status and API call quota for authenticated requests.

    Returns:
        None if allowed, otherwise a tuple of (json_response, status_code)
    """
    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter_by(id=user.tenant_id).first()
        if not tenant:
            return jsonify({"error": "Tenant not found"}), 500

        status_response = _evaluate_tenant_status(tenant, request.method)
        if status_response:
            return status_response

        usage = _ensure_usage_record(session, tenant.id)
        _reset_usage_windows(usage, session)

        limits = get_plan_limits(tenant.plan_tier, session)
        pending_calls = await usage_tracker.get_pending_api_calls(tenant.id)
        current_calls = usage.api_calls_today + pending_calls

        if limits['max_api_calls_per_day'] != -1 and current_calls >= limits['max_api_calls_per_day']:
            return jsonify({
                "error": "API limit exceeded",
                "message": f"You've reached the daily API limit for your {tenant.plan_tier} plan.",
                "current_usage": usage.api_calls_today,
                "pending_usage": pending_calls,
                "limit": limits['max_api_calls_per_day'],
                "plan_tier": tenant.plan_tier,
                "upgrade_url": "/billing/upgrade"
            }), 429

        return None
    finally:
        session.close()


async def check_file_upload_quota(tenant_id: int, file_size: int) -> tuple:
    """
    Check if a file upload would exceed storage quota.

    Args:
        tenant_id: The tenant ID
        file_size: Size of file to upload in bytes

    Returns:
        tuple: (allowed: bool, error_message: str or None)
    """
    session = SessionLocal()
    try:
        tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()

        if not tenant or not usage:
            return False, "Tenant not found"

        limits = get_plan_limits(tenant.plan_tier, session)

        # Check if upload would exceed limit
        new_total = usage.storage_bytes + file_size

        if limits['max_storage_bytes'] == 0:
            # Free tier - no file storage allowed
            return False, f"File storage is not available on the {tenant.plan_tier} plan. Please upgrade to upload files."

        if limits['max_storage_bytes'] != -1 and new_total > limits['max_storage_bytes']:
            current_gb = round(usage.storage_bytes / (1024**3), 2)
            limit_gb = round(limits['max_storage_bytes'] / (1024**3), 2)
            return False, f"This upload would exceed your storage limit. Current: {current_gb}GB, Limit: {limit_gb}GB. Please upgrade your plan."

        return True, None

    finally:
        session.close()
