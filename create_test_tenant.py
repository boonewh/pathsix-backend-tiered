"""
Create a test tenant and user for testing tiered pricing functionality.

This creates:
- A test tenant on the 'starter' plan
- A test user with admin role
- Initial usage tracking record
"""

from app.database import SessionLocal, init_db
from app.models import Tenant, TenantStatus, User, Role, TenantUsage
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import bcrypt


def create_test_tenant():
    """Create a test tenant and user for development."""

    session = SessionLocal()
    try:
        # Check if test tenant already exists
        existing_tenant = session.query(Tenant).filter_by(id=999).first()
        if existing_tenant:
            print("Test tenant (ID 999) already exists. Deleting and recreating...")
            # Delete existing test data
            session.query(TenantUsage).filter_by(tenant_id=999).delete()
            session.query(User).filter_by(tenant_id=999).delete()
            session.query(Tenant).filter_by(id=999).delete()
            session.commit()

        # Create test tenant
        print("\n=== Creating Test Tenant ===")
        tenant = Tenant(
            id=999,
            plan_tier='starter',  # Start with starter plan
            status=TenantStatus.active,
            company_name='Test Company',
            billing_email='test@example.com',
            created_at=datetime.utcnow()
        )
        session.add(tenant)
        session.flush()

        print(f"[OK] Created tenant: {tenant.company_name} (ID: {tenant.id})")
        print(f"  Plan: {tenant.plan_tier}")
        print(f"  Status: {tenant.status.value}")

        # Create usage tracking record
        usage = TenantUsage(
            tenant_id=999,
            storage_bytes=0,
            db_record_count=0,
            api_calls_today=0,
            emails_this_month=0,
            api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
            emails_reset_at=(datetime.utcnow() + relativedelta(months=1)).replace(day=1)
        )
        session.add(usage)
        session.flush()

        print(f"[OK] Created usage tracking for tenant {tenant.id}")

        # Get or create admin role
        admin_role = session.query(Role).filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin')
            session.add(admin_role)
            session.flush()
            print("[OK] Created 'admin' role")

        # Create test user
        password = 'testpass123'
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        user = User(
            tenant_id=999,
            email='test@example.com',
            password_hash=password_hash,
            is_active=True,
            email_verified=True,
            email_verified_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        user.roles.append(admin_role)
        session.add(user)
        session.flush()

        print(f"[OK] Created user: {user.email}")
        print(f"  Password: {password}")
        print(f"  Roles: admin")

        session.commit()

        print("\n=== Test Account Created Successfully ===\n")
        print("Login credentials:")
        print(f"  Email: test@example.com")
        print(f"  Password: testpass123")
        print(f"  Tenant ID: 999")
        print(f"  Plan: starter")
        print()
        print("Starter Plan Limits:")
        print("  - Users: 3")
        print("  - Storage: 2 GB")
        print("  - DB Records: 5,000")
        print("  - API Calls/Day: 5,000")
        print("  - Emails/Month: 100")
        print()
        print("You can now test:")
        print("  1. Login with these credentials")
        print("  2. Check /api/billing/usage endpoint")
        print("  3. Try creating records to test quota enforcement")
        print("  4. Try uploading files to test storage quota")
        print()

    except Exception as e:
        session.rollback()
        print(f"Error creating test tenant: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Ensure database is initialized
    init_db()

    # Create test tenant
    create_test_tenant()
