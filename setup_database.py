"""
Database Setup Script for PathSix CRM Backend
Initializes required data for development and production.

Run this script after creating the database tables with migrations.
"""
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from app.database import SessionLocal
from app.models import Role, PlanLimit, User, Tenant, TenantUsage, TenantStatus
from app.utils.auth_utils import hash_password

def setup_roles(session):
    """Create required roles if they don't exist."""
    print("\n[ROLES] Setting up roles...")

    required_roles = ['admin', 'file_uploads']
    existing_roles = {role.name for role in session.query(Role).all()}

    roles_created = 0
    for role_name in required_roles:
        if role_name not in existing_roles:
            role = Role(name=role_name)
            session.add(role)
            roles_created += 1
            print(f"  [OK] Created role: {role_name}")
        else:
            print(f"  [SKIP] Role already exists: {role_name}")

    if roles_created > 0:
        session.commit()
        print(f"  [OK] {roles_created} new role(s) created")
    else:
        print("  [OK] All roles already exist")

def setup_plan_limits(session):
    """Create plan limits if they don't exist."""
    print("\n[PLANS] Setting up plan limits...")

    existing_plans = {plan.plan_tier for plan in session.query(PlanLimit).all()}

    plan_data = [
        {
            'plan_tier': 'free',
            'max_users': 1,
            'max_storage_bytes': 0,  # 0 GB
            'max_db_records': 25,
            'max_api_calls_per_day': 100,
            'max_emails_per_month': 3,
            'features': {}
        },
        {
            'plan_tier': 'starter',
            'max_users': 3,
            'max_storage_bytes': 2 * 1024 * 1024 * 1024,  # 2 GB
            'max_db_records': 5000,
            'max_api_calls_per_day': 5000,
            'max_emails_per_month': 100,
            'features': {'file_uploads': True}
        },
        {
            'plan_tier': 'business',
            'max_users': 10,
            'max_storage_bytes': 25 * 1024 * 1024 * 1024,  # 25 GB
            'max_db_records': 50000,
            'max_api_calls_per_day': 50000,
            'max_emails_per_month': 1000,
            'features': {'file_uploads': True, 'advanced_reports': True}
        },
        {
            'plan_tier': 'enterprise',
            'max_users': -1,  # Unlimited
            'max_storage_bytes': 250 * 1024 * 1024 * 1024,  # 250 GB hard cap
            'max_db_records': 500000,
            'max_api_calls_per_day': -1,  # Unlimited
            'max_emails_per_month': 10000,
            'features': {'file_uploads': True, 'advanced_reports': True, 'api_access': True}
        }
    ]

    plans_created = 0
    for plan in plan_data:
        if plan['plan_tier'] not in existing_plans:
            plan_limit = PlanLimit(**plan)
            session.add(plan_limit)
            plans_created += 1
            print(f"  [OK] Created plan: {plan['plan_tier']}")
        else:
            print(f"  [SKIP] Plan already exists: {plan['plan_tier']}")

    if plans_created > 0:
        session.commit()
        print(f"  [OK] {plans_created} new plan(s) created")
    else:
        print("  [OK] All plans already exist")

def create_test_admin(session):
    """Create a platform owner admin account with known credentials.

    This account has the 'admin' role which grants access to:
    - Admin analytics endpoints (ALL tenant visibility, revenue metrics)
    - Platform-wide monitoring and business intelligence

    Regular users signing up via /api/signup do NOT get admin role.
    """
    print("\n[USER] Setting up platform owner admin account...")

    test_email = "admin@pathsix.local"
    test_password = "PathSix2025!"

    # Check if user already exists
    existing_user = session.query(User).filter_by(email=test_email).first()
    if existing_user:
        print(f"  [SKIP] Platform owner account already exists: {test_email}")
        print(f"\n  [LOGIN] PLATFORM OWNER LOGIN CREDENTIALS:")
        print(f"     Email: {test_email}")
        print(f"     Password: {test_password}")
        print(f"     Access: Admin analytics + full platform visibility")
        return

    # Create tenant for platform owner (free tier for development/testing)
    tenant = Tenant(
        plan_tier='free',
        status=TenantStatus.active,
        billing_email=test_email,
        company_name='PathSix Test Company',
        created_at=datetime.utcnow()
    )
    session.add(tenant)
    session.flush()

    # Create tenant usage tracking
    usage = TenantUsage(
        tenant_id=tenant.id,
        storage_bytes=0,
        db_record_count=0,
        api_calls_today=0,
        emails_this_month=0,
        api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
        emails_reset_at=datetime.utcnow() + relativedelta(months=1)
    )
    session.add(usage)

    # Create admin user
    user = User(
        tenant_id=tenant.id,
        email=test_email,
        password_hash=hash_password(test_password),
        email_verified=True,  # Pre-verified for testing
        created_at=datetime.utcnow()
    )
    session.add(user)
    session.flush()

    # Assign admin role
    admin_role = session.query(Role).filter_by(name='admin').first()
    if admin_role:
        user.roles.append(admin_role)

    # Assign file_uploads role
    file_uploads_role = session.query(Role).filter_by(name='file_uploads').first()
    if file_uploads_role:
        user.roles.append(file_uploads_role)

    session.commit()

    print(f"  [OK] Created platform owner account")
    print(f"  [OK] Assigned roles: admin, file_uploads")
    print(f"  [OK] Email verified: True")
    print(f"  [OK] Tenant ID: {tenant.id}")
    print(f"\n  [LOGIN] PLATFORM OWNER LOGIN CREDENTIALS:")
    print(f"     Email: {test_email}")
    print(f"     Password: {test_password}")
    print(f"     Access: Admin analytics + full platform visibility")

def main():
    """Run all setup tasks."""
    print("=" * 60)
    print("PathSix CRM - Database Setup")
    print("=" * 60)

    session = SessionLocal()
    try:
        setup_roles(session)
        setup_plan_limits(session)
        create_test_admin(session)

        print("\n" + "=" * 60)
        print("[OK] Database setup complete!")
        print("=" * 60)
        print("\n[NEXT] Next Steps:")
        print("   1. Start the server: python run.py")
        print("   2. Login with admin@pathsix.local / PathSix2025!")
        print("   3. Test signup flow with a new email")
        print("   4. Configure Stripe environment variables for billing")
        print("\n")

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Error during setup: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    main()
