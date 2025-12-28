"""
Quota enforcement middleware for tiered pricing.

This middleware runs BEFORE request handlers to check if tenant has exceeded quotas.
For read-only mode, it blocks POST/PUT/DELETE but allows GET.
"""

from functools import wraps
from quart import request, jsonify
from app.database import SessionLocal
from app.models import Tenant, TenantUsage, TenantStatus
from datetime import datetime
from app.utils.plan_utils import get_plan_limits


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

                # Check tenant status
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

                # Block writes if in read-only mode
                if tenant.status == TenantStatus.read_only:
                    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
                        return jsonify({
                            "error": "Quota exceeded",
                            "message": "Your account has exceeded quota limits and is in read-only mode. Please upgrade your plan.",
                            "status": "read_only",
                            "upgrade_url": "/billing/upgrade"
                        }), 403

                # Get usage data
                usage = session.query(TenantUsage).filter_by(tenant_id=user.tenant_id).first()
                if not usage:
                    # Initialize usage if missing
                    from datetime import timedelta
                    from dateutil.relativedelta import relativedelta
                    usage = TenantUsage(
                        tenant_id=user.tenant_id,
                        api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
                        emails_reset_at=(datetime.utcnow() + relativedelta(months=1)).replace(day=1)
                    )
                    session.add(usage)
                    session.commit()

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
                    # Reset counter if needed
                    if datetime.utcnow() > usage.emails_reset_at:
                        usage.emails_this_month = 0
                        # Reset to first day of next month
                        from dateutil.relativedelta import relativedelta
                        usage.emails_reset_at = (datetime.utcnow() + relativedelta(months=1)).replace(day=1)
                        session.commit()

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
