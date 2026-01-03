"""
Admin Analytics Routes - Platform Owner Visibility

Provides analytics and insights for the platform owner to monitor:
- Customer counts by tier
- Revenue metrics (MRR, churn, etc.)
- Usage patterns across customers
- Customers approaching quota limits
- Health metrics for business decisions

All endpoints require admin role.
"""

from quart import Blueprint, jsonify
from sqlalchemy import func, case, and_, or_
from datetime import datetime, timedelta
from app.utils.auth_utils import requires_auth
from app.models import Tenant, TenantUsage, Subscription, User, PlanLimit, TenantStatus
from app.database import SessionLocal

admin_analytics_bp = Blueprint('admin_analytics', __name__)

# Pricing constants (match your tiers)
TIER_PRICES = {
    'free': 0,
    'starter': 14.99,
    'business': 79,
    'enterprise': 499
}


@admin_analytics_bp.route('/api/admin/analytics/overview', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_overview(user):
    """
    Get high-level platform overview metrics.

    Returns:
    - Total tenant count
    - Breakdown by tier
    - Active vs suspended tenants
    - MRR (Monthly Recurring Revenue)
    - Signups in last 30 days
    """
    session = SessionLocal()
    try:
        # Total tenants
        total_tenants = session.query(Tenant).count()

        # Breakdown by tier
        tier_breakdown = session.query(
            Tenant.plan_tier,
            func.count(Tenant.id).label('count')
        ).group_by(Tenant.plan_tier).all()

        by_tier = {tier: count for tier, count in tier_breakdown}

        # Active vs suspended
        active_count = session.query(Tenant).filter_by(status=TenantStatus.active).count()
        suspended_count = session.query(Tenant).filter(
            or_(
                Tenant.status == TenantStatus.suspended,
                Tenant.status == TenantStatus.read_only
            )
        ).count()

        # Calculate MRR (Monthly Recurring Revenue)
        mrr = 0
        for tier, count in by_tier.items():
            mrr += count * TIER_PRICES.get(tier, 0)

        # Signups in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_signups = session.query(Tenant).filter(
            Tenant.created_at >= thirty_days_ago
        ).count()

        return jsonify({
            'total_tenants': total_tenants,
            'by_tier': by_tier,
            'active_tenants': active_count,
            'suspended_tenants': suspended_count,
            'mrr': round(mrr, 2),
            'signups_last_30_days': recent_signups,
            'generated_at': datetime.utcnow().isoformat()
        }), 200

    finally:
        session.close()


@admin_analytics_bp.route('/api/admin/analytics/tiers', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_tier_breakdown(user):
    """
    Get detailed breakdown by pricing tier.

    Returns for each tier:
    - Customer count
    - Revenue contribution
    - Average usage percentage
    - Average records used
    - Churned customers in last 30 days
    """
    session = SessionLocal()
    try:
        tiers = []

        for tier_name in ['free', 'starter', 'business', 'enterprise']:
            # Get all tenants on this tier
            tenants_on_tier = session.query(Tenant).filter_by(plan_tier=tier_name).all()
            count = len(tenants_on_tier)

            if count == 0:
                tiers.append({
                    'tier': tier_name,
                    'count': 0,
                    'revenue': 0,
                    'avg_usage_percent': 0,
                    'avg_records': 0,
                    'churned_last_month': 0
                })
                continue

            # Revenue for this tier
            revenue = count * TIER_PRICES[tier_name]

            # Get usage stats
            tenant_ids = [t.id for t in tenants_on_tier]
            usage_records = session.query(TenantUsage).filter(
                TenantUsage.tenant_id.in_(tenant_ids)
            ).all()

            # Get plan limits for this tier
            plan_limit = session.query(PlanLimit).filter_by(plan_tier=tier_name).first()

            # Calculate average usage percentage
            total_usage_percent = 0
            total_records = 0

            for usage in usage_records:
                if plan_limit and plan_limit.max_db_records > 0:
                    usage_percent = (usage.db_record_count / plan_limit.max_db_records) * 100
                    total_usage_percent += usage_percent
                total_records += usage.db_record_count

            avg_usage_percent = total_usage_percent / len(usage_records) if usage_records else 0
            avg_records = total_records / len(usage_records) if usage_records else 0

            # Churned in last 30 days (suspended/cancelled)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            churned = session.query(Tenant).filter(
                and_(
                    Tenant.plan_tier == tier_name,
                    or_(
                        Tenant.status == TenantStatus.suspended,
                        Tenant.status == TenantStatus.cancelled
                    ),
                    Tenant.updated_at >= thirty_days_ago
                )
            ).count()

            tiers.append({
                'tier': tier_name,
                'count': count,
                'revenue': round(revenue, 2),
                'avg_usage_percent': round(avg_usage_percent, 1),
                'avg_records': round(avg_records, 0),
                'churned_last_month': churned
            })

        return jsonify({'tiers': tiers}), 200

    finally:
        session.close()


@admin_analytics_bp.route('/api/admin/analytics/usage', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_usage_patterns(user):
    """
    Get usage pattern insights.

    Returns:
    - Customers approaching quota limits (>80%)
    - Average usage by tier
    - High-usage customers (potential upsell targets)
    """
    session = SessionLocal()
    try:
        approaching_limits = []

        # Get all tenants with their usage and limits
        tenants = session.query(Tenant).filter_by(status=TenantStatus.active).all()

        for tenant in tenants:
            usage = session.query(TenantUsage).filter_by(tenant_id=tenant.id).first()
            plan_limit = session.query(PlanLimit).filter_by(plan_tier=tenant.plan_tier).first()

            if not usage or not plan_limit:
                continue

            # Check if approaching record limit (>80%)
            if plan_limit.max_db_records > 0:
                usage_percent = (usage.db_record_count / plan_limit.max_db_records) * 100

                if usage_percent >= 80:
                    approaching_limits.append({
                        'tenant_id': tenant.id,
                        'email': tenant.billing_email,
                        'company_name': tenant.company_name,
                        'tier': tenant.plan_tier,
                        'quota_type': 'records',
                        'used': usage.db_record_count,
                        'limit': plan_limit.max_db_records,
                        'percent_used': round(usage_percent, 1)
                    })

            # Check if approaching storage limit (>80%)
            if plan_limit.max_storage_bytes > 0:
                storage_percent = (usage.storage_bytes / plan_limit.max_storage_bytes) * 100

                if storage_percent >= 80:
                    approaching_limits.append({
                        'tenant_id': tenant.id,
                        'email': tenant.billing_email,
                        'company_name': tenant.company_name,
                        'tier': tenant.plan_tier,
                        'quota_type': 'storage',
                        'used': usage.storage_bytes,
                        'limit': plan_limit.max_storage_bytes,
                        'percent_used': round(storage_percent, 1)
                    })

        # Sort by highest usage percentage
        approaching_limits.sort(key=lambda x: x['percent_used'], reverse=True)

        return jsonify({
            'approaching_limits': approaching_limits[:50],  # Top 50
            'total_at_risk': len(approaching_limits)
        }), 200

    finally:
        session.close()


@admin_analytics_bp.route('/api/admin/analytics/customers', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_customer_list(user):
    """
    Get paginated customer list with filters.

    Query Parameters:
    - tier: Filter by tier (free, starter, business, enterprise)
    - status: Filter by status (active, suspended, read_only, cancelled)
    - sort: Sort by (created_asc, created_desc, usage_asc, usage_desc, revenue_desc)
    - page: Page number (default 1)
    - limit: Items per page (default 25, max 100)
    """
    from quart import request

    # Get query parameters
    tier_filter = request.args.get('tier')
    status_filter = request.args.get('status')
    sort_by = request.args.get('sort', 'created_desc')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 25)), 100)

    session = SessionLocal()
    try:
        # Build base query
        query = session.query(Tenant)

        # Apply filters
        if tier_filter:
            query = query.filter_by(plan_tier=tier_filter)

        if status_filter:
            query = query.filter_by(status=TenantStatus[status_filter])

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if sort_by == 'created_asc':
            query = query.order_by(Tenant.created_at.asc())
        elif sort_by == 'created_desc':
            query = query.order_by(Tenant.created_at.desc())
        elif sort_by == 'usage_desc':
            # Join with usage and sort by records
            query = query.join(TenantUsage).order_by(TenantUsage.db_record_count.desc())
        elif sort_by == 'revenue_desc':
            # Sort by tier price (enterprise, business, starter, free)
            tier_order = case(
                (Tenant.plan_tier == 'enterprise', 4),
                (Tenant.plan_tier == 'business', 3),
                (Tenant.plan_tier == 'starter', 2),
                (Tenant.plan_tier == 'free', 1)
            )
            query = query.order_by(tier_order.desc())

        # Pagination
        offset = (page - 1) * limit
        tenants = query.offset(offset).limit(limit).all()

        # Build customer data
        customers = []
        for tenant in tenants:
            usage = session.query(TenantUsage).filter_by(tenant_id=tenant.id).first()

            # Get primary user email if billing_email not set
            primary_user = session.query(User).filter_by(tenant_id=tenant.id).order_by(User.id).first()
            email = tenant.billing_email or (primary_user.email if primary_user else None)

            customers.append({
                'tenant_id': tenant.id,
                'email': email,
                'company_name': tenant.company_name,
                'tier': tenant.plan_tier,
                'status': tenant.status.value,
                'created_at': tenant.created_at.isoformat() if tenant.created_at else None,
                'records': usage.db_record_count if usage else 0,
                'storage_bytes': usage.storage_bytes if usage else 0,
                'storage_gb': round(usage.storage_bytes / (1024**3), 2) if usage else 0,
                'mrr': TIER_PRICES.get(tenant.plan_tier, 0),
                'stripe_customer_id': tenant.stripe_customer_id
            })

        return jsonify({
            'customers': customers,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit  # Ceiling division
        }), 200

    finally:
        session.close()


@admin_analytics_bp.route('/api/admin/analytics/revenue', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_revenue_metrics(user):
    """
    Get revenue tracking and projections.

    Returns:
    - Current MRR (Monthly Recurring Revenue)
    - MRR breakdown by tier
    - Monthly trend (last 6 months)
    - Churn rate
    - Customer LTV estimates
    """
    session = SessionLocal()
    try:
        # Current MRR
        tier_breakdown = session.query(
            Tenant.plan_tier,
            func.count(Tenant.id).label('count')
        ).filter_by(status=TenantStatus.active).group_by(Tenant.plan_tier).all()

        mrr_by_tier = {}
        total_mrr = 0

        for tier, count in tier_breakdown:
            tier_revenue = count * TIER_PRICES.get(tier, 0)
            mrr_by_tier[tier] = round(tier_revenue, 2)
            total_mrr += tier_revenue

        # Monthly trend (last 6 months)
        monthly_trend = []
        for i in range(5, -1, -1):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
            month_end = (month_start + timedelta(days=32)).replace(day=1)

            # Count active tenants in that month
            tenants_that_month = session.query(
                Tenant.plan_tier,
                func.count(Tenant.id).label('count')
            ).filter(
                and_(
                    Tenant.created_at <= month_end,
                    or_(
                        Tenant.status == TenantStatus.active,
                        Tenant.updated_at >= month_start  # Include if was active during month
                    )
                )
            ).group_by(Tenant.plan_tier).all()

            month_revenue = sum(
                count * TIER_PRICES.get(tier, 0)
                for tier, count in tenants_that_month
            )

            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': round(month_revenue, 2)
            })

        # Churn rate (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        churned = session.query(Tenant).filter(
            and_(
                or_(
                    Tenant.status == TenantStatus.suspended,
                    Tenant.status == TenantStatus.cancelled
                ),
                Tenant.updated_at >= thirty_days_ago
            )
        ).count()

        active_start_of_month = session.query(Tenant).filter(
            Tenant.created_at < thirty_days_ago
        ).count()

        churn_rate = (churned / active_start_of_month * 100) if active_start_of_month > 0 else 0

        # Average LTV (simplified: MRR / churn_rate * 100, or 12 months if no churn)
        avg_customer_value = total_mrr / max(tier_breakdown.__len__(), 1)
        estimated_ltv = avg_customer_value * 12 if churn_rate == 0 else (avg_customer_value / (churn_rate / 100))

        return jsonify({
            'mrr': round(total_mrr, 2),
            'by_tier': mrr_by_tier,
            'monthly_trend': monthly_trend,
            'churn_rate': round(churn_rate, 2),
            'estimated_ltv': round(estimated_ltv, 2),
            'arr': round(total_mrr * 12, 2)  # Annual Recurring Revenue
        }), 200

    finally:
        session.close()


@admin_analytics_bp.route('/api/admin/analytics/health', methods=['GET'])
@requires_auth(roles=['admin'])
async def get_platform_health(user):
    """
    Get platform health indicators.

    Returns:
    - Failed payments (needs attention)
    - Suspended tenants (revenue at risk)
    - High-value customers (top 10 by usage)
    - Upsell opportunities (high usage on lower tiers)
    """
    session = SessionLocal()
    try:
        # Failed payments (tenants with payment_failed status)
        failed_payments = session.query(Tenant).filter_by(
            status=TenantStatus.suspended
        ).count()

        # Suspended tenants (revenue at risk)
        suspended = session.query(Tenant).filter(
            or_(
                Tenant.status == TenantStatus.suspended,
                Tenant.status == TenantStatus.read_only
            )
        ).all()

        revenue_at_risk = sum(TIER_PRICES.get(t.plan_tier, 0) for t in suspended)

        # High-value customers (top 10 by tier + usage)
        high_value = []
        enterprise_tenants = session.query(Tenant).filter_by(
            plan_tier='enterprise',
            status=TenantStatus.active
        ).limit(5).all()

        for tenant in enterprise_tenants:
            usage = session.query(TenantUsage).filter_by(tenant_id=tenant.id).first()
            high_value.append({
                'tenant_id': tenant.id,
                'email': tenant.billing_email,
                'company_name': tenant.company_name,
                'tier': tenant.plan_tier,
                'mrr': TIER_PRICES['enterprise'],
                'records': usage.db_record_count if usage else 0
            })

        # Upsell opportunities (high usage on starter/business)
        upsell_candidates = []

        # Starter users using >70% of quota
        starter_tenants = session.query(Tenant).filter_by(
            plan_tier='starter',
            status=TenantStatus.active
        ).all()

        starter_limit = session.query(PlanLimit).filter_by(plan_tier='starter').first()

        for tenant in starter_tenants:
            usage = session.query(TenantUsage).filter_by(tenant_id=tenant.id).first()
            if usage and starter_limit and starter_limit.max_db_records > 0:
                usage_percent = (usage.db_record_count / starter_limit.max_db_records) * 100
                if usage_percent > 70:
                    upsell_candidates.append({
                        'tenant_id': tenant.id,
                        'email': tenant.billing_email,
                        'company_name': tenant.company_name,
                        'current_tier': 'starter',
                        'suggested_tier': 'business',
                        'usage_percent': round(usage_percent, 1)
                    })

        return jsonify({
            'failed_payments_count': failed_payments,
            'suspended_count': len(suspended),
            'revenue_at_risk': round(revenue_at_risk, 2),
            'high_value_customers': high_value,
            'upsell_opportunities': upsell_candidates[:10]  # Top 10
        }), 200

    finally:
        session.close()
