"""
RQ (Redis Queue) worker infrastructure for background jobs.
"""
import redis
from rq import Queue
from app.config import REDIS_URL

# Redis connection (shared across all queues)
redis_conn = redis.from_url(REDIS_URL)

# Queue for backup/restore jobs
backup_queue = Queue('backups', connection=redis_conn, default_timeout='1h')