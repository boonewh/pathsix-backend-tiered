"""
Plan utilities for tiered pricing system.

Provides functions for:
- Querying plan limits with caching
- Checking quota status
- Updating tenant status based on usage
"""

from app.database import SessionLocal
from app.models import PlanLimit, TenantUsage, Tenant, TenantStatus
from datetime import datetime, timedelta
from sqlalchemy import func

# In-memory cache for plan limits (refreshed periodically)
_plan_limits_cache = {}
_cache_timestamp = None
CACHE_TTL_SECONDS = 300  # 5 minutes


def get_plan_limits(plan_tier: str, session=None) -> dict:
    """
    Get limits for a given plan tier with caching.

    Args:
        plan_tier: One of 'free', 'starter', 'business', 'enterprise'
        session: Optional database session (will create one if not provided)

    Returns:
        dict with keys:
            - max_users
            - max_storage_bytes
            - max_db_records
            - max_api_calls_per_day
            - max_emails_per_month
            - features
    """
    global _plan_limits_cache, _cache_timestamp

    # Check cache
    now = datetime.utcnow()
    if _cache_timestamp and (now - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
        if plan_tier in _plan_limits_cache:
            return _plan_limits_cache[plan_tier]

    # Query database
    should_close = False
    if not session:
        session = SessionLocal()
        should_close = True

    try:
        plan_limit = session.query(PlanLimit).filter_by(plan_tier=plan_tier).first()

        if not plan_limit:
            # Return default limits if not found
            return _get_default_limits(plan_tier)

        limits = {
            "max_users": plan_limit.max_users,
            "max_storage_bytes": plan_limit.max_storage_bytes,
            "max_db_records": plan_limit.max_db_records,
            "max_api_calls_per_day": plan_limit.max_api_calls_per_day,
            "max_emails_per_month": plan_limit.max_emails_per_month,
            "features": plan_limit.features or {}
        }

        # Update cache
        _plan_limits_cache[plan_tier] = limits
        _cache_timestamp = now

        return limits

    finally:
        if should_close:
            session.close()


def _get_default_limits(plan_tier: str) -> dict:
    """
    Hardcoded defaults as fallback.
    These match the confirmed tier structure from the plan.
    """
    defaults = {
        "free": {
            "max_users": 1,
            "max_storage_bytes": 0,  # No file storage
            "max_db_records": 100,
            "max_api_calls_per_day": 500,
            "max_emails_per_month": 10,
            "features": {}
        },
        "starter": {
            "max_users": 3,
            "max_storage_bytes": 2 * 1024**3,  # 2GB
            "max_db_records": 5000,
            "max_api_calls_per_day": 5000,
            "max_emails_per_month": 100,
            "features": {}
        },
        "business": {
            "max_users": 10,
            "max_storage_bytes": 25 * 1024**3,  # 25GB
            "max_db_records": 50000,
            "max_api_calls_per_day": 25000,
            "max_emails_per_month": 1000,
            "features": {"advanced_reporting": True}
        },
        "enterprise": {
            "max_users": -1,  # Unlimited
            "max_storage_bytes": 250 * 1024**3,  # 250GB hard cap
            "max_db_records": 500000,
            "max_api_calls_per_day": 100000,
            "max_emails_per_month": 5000,
            "features": {"advanced_reporting": True, "api_access": True, "priority_support": True}
        }
    }
    return defaults.get(plan_tier, defaults["free"])


def update_usage_limits_cache(tenant_id: int, plan_tier: str, session):
    """
    Update cached limits in TenantUsage table for faster lookups.

    This denormalizes the plan limits into the usage table to avoid
    joining with plan_limits on every quota check.

    Args:
        tenant_id: The tenant ID
        plan_tier: The plan tier
        session: Database session
    """
    limits = get_plan_limits(plan_tier, session)

    usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
    if usage:
        usage.cached_max_storage = limits["max_storage_bytes"]
        usage.cached_max_records = limits["max_db_records"]
        usage.cached_max_api_calls = limits["max_api_calls_per_day"]
        usage.cached_max_emails = limits["max_emails_per_month"]
        usage.cached_limits_updated_at = datetime.utcnow()


def check_and_update_tenant_status(tenant_id: int, session):
    """
    Check if tenant has exceeded quotas and update status accordingly.

    This should be called:
    - After record creation/deletion
    - After file upload/deletion
    - Periodically via cron job

    Args:
        tenant_id: The tenant ID
        session: Database session
    """
    tenant = session.query(Tenant).filter_by(id=tenant_id).first()
    usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()

    if not tenant or not usage:
        return

    limits = get_plan_limits(tenant.plan_tier, session)

    # Check if any quota exceeded
    quota_exceeded = False

    if limits["max_storage_bytes"] != -1 and usage.storage_bytes >= limits["max_storage_bytes"]:
        quota_exceeded = True

    if limits["max_db_records"] != -1 and usage.db_record_count >= limits["max_db_records"]:
        quota_exceeded = True

    # Update tenant status
    if quota_exceeded and tenant.status == TenantStatus.active:
        tenant.status = TenantStatus.read_only
        session.commit()

        # Send notification (import here to avoid circular dependency)
        try:
            from app.utils.email_utils import send_email
            import asyncio
            if tenant.billing_email:
                # Fire and forget - don't await
                asyncio.create_task(send_email(
                    subject="PathSix CRM - Quota Limit Reached",
                    recipient=tenant.billing_email,
                    body=f"Your PathSix CRM account has reached quota limits and is now in read-only mode.\n\nPlease upgrade your plan to continue adding data.\n\nUpgrade here: https://app.pathsix.com/billing"
                ))
        except Exception as e:
            # Don't fail the quota check if email fails
            print(f"Failed to send quota warning email: {e}")

    elif not quota_exceeded and tenant.status == TenantStatus.read_only:
        # Restore to active if under quota (e.g., after deleting data)
        tenant.status = TenantStatus.active
        session.commit()


def recalculate_storage_usage(tenant_id: int, session=None):
    """
    Recalculate total storage usage from File table.

    Args:
        tenant_id: The tenant ID
        session: Optional database session

    Returns:
        int: Total storage in bytes
    """
    from app.models import File

    should_close = False
    if not session:
        session = SessionLocal()
        should_close = True

    try:
        total_bytes = session.query(func.sum(File.size))\
            .filter(File.tenant_id == tenant_id)\
            .scalar() or 0

        usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
        if usage:
            usage.storage_bytes = total_bytes
            usage.updated_at = datetime.utcnow()
            session.commit()

        return total_bytes

    finally:
        if should_close:
            session.close()


def recalculate_record_count(tenant_id: int, session=None):
    """
    Recalculate total record count from all entity tables.

    Counts non-deleted records from:
    - Clients
    - Leads
    - Contacts
    - Projects
    - Interactions

    Args:
        tenant_id: The tenant ID
        session: Optional database session

    Returns:
        int: Total record count
    """
    from app.models import Client, Lead, Contact, Project, Interaction

    should_close = False
    if not session:
        session = SessionLocal()
        should_close = True

    try:
        total = 0

        # Count clients (non-deleted)
        total += session.query(func.count(Client.id))\
            .filter(Client.tenant_id == tenant_id)\
            .filter(Client.deleted_at == None)\
            .scalar() or 0

        # Count leads (non-deleted)
        total += session.query(func.count(Lead.id))\
            .filter(Lead.tenant_id == tenant_id)\
            .filter(Lead.deleted_at == None)\
            .scalar() or 0

        # Count contacts (no soft delete)
        total += session.query(func.count(Contact.id))\
            .filter(Contact.tenant_id == tenant_id)\
            .scalar() or 0

        # Count projects (non-deleted)
        total += session.query(func.count(Project.id))\
            .filter(Project.tenant_id == tenant_id)\
            .filter(Project.deleted_at == None)\
            .scalar() or 0

        # Count interactions (no soft delete)
        total += session.query(func.count(Interaction.id))\
            .filter(Interaction.tenant_id == tenant_id)\
            .scalar() or 0

        usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
        if usage:
            usage.db_record_count = total
            usage.updated_at = datetime.utcnow()
            session.commit()

        return total

    finally:
        if should_close:
            session.close()


def get_usage_percentage(current: int, limit: int) -> float:
    """
    Calculate usage percentage.

    Args:
        current: Current usage value
        limit: Maximum limit (-1 for unlimited)

    Returns:
        float: Percentage (0-100), or 0 if unlimited
    """
    if limit == -1:
        return 0.0
    if limit == 0:
        return 100.0 if current > 0 else 0.0
    return min(100.0, (current / limit) * 100)


def is_feature_enabled(tenant_id: int, feature_name: str, session=None) -> bool:
    """
    Check if a feature is enabled for a tenant's plan.

    Args:
        tenant_id: The tenant ID
        feature_name: Feature name (e.g., 'advanced_reporting', 'api_access')
        session: Optional database session

    Returns:
        bool: True if feature is enabled
    """
    should_close = False
    if not session:
        session = SessionLocal()
        should_close = True

    try:
        tenant = session.query(Tenant).filter_by(id=tenant_id).first()
        if not tenant:
            return False

        limits = get_plan_limits(tenant.plan_tier, session)
        features = limits.get("features", {})

        return features.get(feature_name, False)

    finally:
        if should_close:
            session.close()
