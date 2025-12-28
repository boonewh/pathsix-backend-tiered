"""
Usage tracking middleware for monitoring tenant resource consumption.

This runs AFTER successful requests to increment usage counters.
Uses async tasks to avoid blocking the response.
"""

from app.database import SessionLocal
from app.models import TenantUsage, File
from datetime import datetime, timedelta
from sqlalchemy import func
import asyncio
from collections import defaultdict


class UsageTracker:
    """Singleton usage tracker with async background updates."""

    _instance = None
    _update_queue = []
    _queue_lock = asyncio.Lock()
    _background_task = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def track_api_call(self, tenant_id: int):
        """
        Increment API call counter for tenant.

        Args:
            tenant_id: The tenant ID
        """
        async with self._queue_lock:
            self._update_queue.append(('api', tenant_id))

    async def track_email_sent(self, tenant_id: int):
        """
        Increment email counter for tenant.

        Args:
            tenant_id: The tenant ID
        """
        async with self._queue_lock:
            self._update_queue.append(('email', tenant_id))

    async def track_record_created(self, tenant_id: int):
        """
        Increment database record counter.

        Args:
            tenant_id: The tenant ID
        """
        async with self._queue_lock:
            self._update_queue.append(('record_add', tenant_id))

    async def track_record_deleted(self, tenant_id: int):
        """
        Decrement database record counter.

        Args:
            tenant_id: The tenant ID
        """
        async with self._queue_lock:
            self._update_queue.append(('record_del', tenant_id))

    async def recalculate_storage(self, tenant_id: int):
        """
        Recalculate total storage usage from File table.

        Args:
            tenant_id: The tenant ID
        """
        session = SessionLocal()
        try:
            total_bytes = session.query(func.sum(File.size))\
                .filter(File.tenant_id == tenant_id)\
                .scalar() or 0

            usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
            if usage:
                usage.storage_bytes = total_bytes
                usage.updated_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error recalculating storage for tenant {tenant_id}: {e}")
        finally:
            session.close()

    async def recalculate_records(self, tenant_id: int):
        """
        Recalculate total record count from all entity tables.

        Args:
            tenant_id: The tenant ID
        """
        from app.models import Client, Lead, Contact, Project, Interaction

        session = SessionLocal()
        try:
            total = 0
            for model in [Client, Lead, Contact, Project, Interaction]:
                # Handle models with deleted_at field
                if hasattr(model, 'deleted_at'):
                    count = session.query(func.count(model.id))\
                        .filter(model.tenant_id == tenant_id)\
                        .filter(model.deleted_at == None)\
                        .scalar() or 0
                else:
                    count = session.query(func.count(model.id))\
                        .filter(model.tenant_id == tenant_id)\
                        .scalar() or 0
                total += count

            usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
            if usage:
                usage.db_record_count = total
                usage.updated_at = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error recalculating records for tenant {tenant_id}: {e}")
        finally:
            session.close()

    async def process_queue(self):
        """
        Background task to process usage updates in batches.
        Processes every 5 seconds to batch updates for performance.
        """
        while True:
            await asyncio.sleep(5)  # Process every 5 seconds

            async with self._queue_lock:
                if not self._update_queue:
                    continue

                batch = self._update_queue[:]
                self._update_queue.clear()

            # Group by tenant_id and type
            updates = defaultdict(lambda: defaultdict(int))
            for type, tenant_id in batch:
                updates[tenant_id][type] += 1

            # Apply updates to database
            session = SessionLocal()
            try:
                for tenant_id, counts in updates.items():
                    usage = session.query(TenantUsage).filter_by(tenant_id=tenant_id).first()
                    if not usage:
                        # Create usage record if missing
                        from dateutil.relativedelta import relativedelta
                        usage = TenantUsage(
                            tenant_id=tenant_id,
                            api_calls_reset_at=datetime.utcnow() + timedelta(days=1),
                            emails_reset_at=(datetime.utcnow() + relativedelta(months=1)).replace(day=1)
                        )
                        session.add(usage)
                        session.flush()

                    # Reset counters if needed
                    now = datetime.utcnow()
                    if now > usage.api_calls_reset_at:
                        usage.api_calls_today = 0
                        usage.api_calls_reset_at = now + timedelta(days=1)

                    if now > usage.emails_reset_at:
                        usage.emails_this_month = 0
                        from dateutil.relativedelta import relativedelta
                        usage.emails_reset_at = (now + relativedelta(months=1)).replace(day=1)

                    # Apply increments
                    if 'api' in counts:
                        usage.api_calls_today += counts['api']

                    if 'email' in counts:
                        usage.emails_this_month += counts['email']

                    if 'record_add' in counts:
                        usage.db_record_count += counts['record_add']

                    if 'record_del' in counts:
                        usage.db_record_count = max(0, usage.db_record_count - counts['record_del'])

                    usage.updated_at = now

                session.commit()
            except Exception as e:
                session.rollback()
                print(f"Error processing usage queue: {e}")
            finally:
                session.close()

    def start_background_processor(self):
        """Start the background queue processor task."""
        if self._background_task is None or self._background_task.done():
            self._background_task = asyncio.create_task(self.process_queue())
            print("[UsageTracker] Background processor started")

    def stop_background_processor(self):
        """Stop the background queue processor task."""
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            print("[UsageTracker] Background processor stopped")


# Global instance
usage_tracker = UsageTracker()
