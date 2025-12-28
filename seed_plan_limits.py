"""
Seed plan limits for tiered pricing system.

This script populates the plan_limits table with the confirmed tier structure:
- Free: $0/mo - 1 user, 0GB storage, 100 records, 500 API calls/day, 10 emails/mo
- Starter: $14.99/mo - 3 users, 2GB storage, 5K records, 5K API calls/day, 100 emails/mo
- Business: $79/mo - 10 users, 25GB storage, 50K records, 25K API calls/day, 1K emails/mo
- Enterprise: $499/mo - Unlimited users, 250GB storage, 500K records, 100K API calls/day, 5K emails/mo
"""

from app.database import SessionLocal, init_db
from app.models import PlanLimit


def seed_plan_limits():
    """Seed the plan_limits table with tier definitions."""

    session = SessionLocal()
    try:
        # Define all plan tiers with their limits
        plans = [
            PlanLimit(
                plan_tier="free",
                max_users=1,
                max_storage_bytes=0,  # No file storage
                max_db_records=100,
                max_api_calls_per_day=500,
                max_emails_per_month=10,
                features={}
            ),
            PlanLimit(
                plan_tier="starter",
                max_users=3,
                max_storage_bytes=2 * 1024**3,  # 2GB
                max_db_records=5000,
                max_api_calls_per_day=5000,
                max_emails_per_month=100,
                features={}
            ),
            PlanLimit(
                plan_tier="business",
                max_users=10,
                max_storage_bytes=25 * 1024**3,  # 25GB
                max_db_records=50000,
                max_api_calls_per_day=25000,
                max_emails_per_month=1000,
                features={"advanced_reporting": True}
            ),
            PlanLimit(
                plan_tier="enterprise",
                max_users=-1,  # Unlimited
                max_storage_bytes=250 * 1024**3,  # 250GB hard cap
                max_db_records=500000,
                max_api_calls_per_day=100000,
                max_emails_per_month=5000,
                features={
                    "advanced_reporting": True,
                    "api_access": True,
                    "priority_support": True
                }
            )
        ]

        # Insert or update each plan
        for plan in plans:
            existing = session.query(PlanLimit).filter_by(plan_tier=plan.plan_tier).first()
            if existing:
                # Update existing plan
                existing.max_users = plan.max_users
                existing.max_storage_bytes = plan.max_storage_bytes
                existing.max_db_records = plan.max_db_records
                existing.max_api_calls_per_day = plan.max_api_calls_per_day
                existing.max_emails_per_month = plan.max_emails_per_month
                existing.features = plan.features
                print(f"Updated plan: {plan.plan_tier}")
            else:
                # Insert new plan
                session.add(plan)
                print(f"Created plan: {plan.plan_tier}")

        session.commit()

        print("\n=== Plan Limits Seeded Successfully ===\n")

        # Display the seeded plans
        all_plans = session.query(PlanLimit).order_by(PlanLimit.id).all()
        for plan in all_plans:
            storage_gb = plan.max_storage_bytes / (1024**3) if plan.max_storage_bytes > 0 else 0
            print(f"{plan.plan_tier.upper()}:")
            print(f"  Users: {plan.max_users if plan.max_users != -1 else 'Unlimited'}")
            print(f"  Storage: {storage_gb}GB")
            print(f"  DB Records: {plan.max_db_records:,}")
            print(f"  API Calls/Day: {plan.max_api_calls_per_day:,}")
            print(f"  Emails/Month: {plan.max_emails_per_month:,}")
            print(f"  Features: {plan.features}")
            print()

    except Exception as e:
        session.rollback()
        print(f"Error seeding plan limits: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    # Ensure database is initialized
    init_db()

    # Seed the plans
    seed_plan_limits()
