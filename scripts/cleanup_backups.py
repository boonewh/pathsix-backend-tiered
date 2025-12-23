#!/usr/bin/env python
"""
Backup cleanup script for Fly.io scheduled machines.

Deletes backups older than BACKUP_RETENTION_DAYS from both database and B2 storage.

Usage:
    python scripts/cleanup_backups.py

Configure as a Fly.io scheduled machine (run weekly):
    flyctl machines run . \
      --app pathsix-crm-backend \
      --schedule weekly \
      --region iad \
      --vm-memory 256 \
      --env DATABASE_URL=... \
      --env BACKUP_S3_ENDPOINT_URL=... \
      --env BACKUP_S3_ACCESS_KEY_ID=... \
      --env BACKUP_S3_SECRET_ACCESS_KEY=... \
      --env BACKUP_S3_BUCKET=... \
      --env BACKUP_RETENTION_DAYS=30 \
      --cmd "python scripts/cleanup_backups.py"
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.workers.backup_jobs import cleanup_old_backups
from app.utils.logging_utils import logger


def main():
    """Run backup cleanup."""
    logger.info("[Cleanup] Starting backup cleanup job")

    try:
        cleanup_old_backups()
        logger.info("[Cleanup] Cleanup completed successfully")
        return 0

    except Exception as e:
        logger.error(f"[Cleanup] Cleanup failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)