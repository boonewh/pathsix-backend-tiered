"""
RQ (Redis Queue) worker infrastructure for background jobs.
"""
import redis
from rq import Queue
from app.config import REDIS_URL
from app.utils.logging_utils import logger

# Redis connection (shared across all queues)
# Gracefully handle missing Redis in development
redis_conn = None
backup_queue = None

try:
    redis_conn = redis.from_url(REDIS_URL)
    # Test the connection
    redis_conn.ping()

    # Queue for backup/restore jobs
    backup_queue = Queue('backups', connection=redis_conn, default_timeout='1h')
    logger.info("[Workers] Redis connection established successfully")
except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
    logger.warning(f"[Workers] Redis not available: {str(e)}")
    logger.warning("[Workers] Background jobs (backups) will not be available")
    logger.warning("[Workers] This is normal for local development without Redis installed")