# Database Backup System - Implementation Complete ✅

## Summary

Production-ready PostgreSQL backup and restore system has been fully implemented with:
- ✅ Redis + RQ background job processing
- ✅ pg_dump custom format + pg_restore
- ✅ GPG AES256 symmetric encryption via subprocess
- ✅ Backblaze B2 storage (separate bucket)
- ✅ Admin-only API endpoints
- ✅ Pre-restore safety backups
- ✅ SHA-256 checksum verification
- ✅ Automatic retention cleanup
- ✅ Fly.io scheduled machine support

## Files Created/Modified

### Configuration & Dependencies
1. ✅ [requirements.txt](requirements.txt) - Added `redis==5.0.1` and `rq==1.16.2`
2. ✅ [Dockerfile](Dockerfile) - Added `postgresql-client` and `gnupg`
3. ✅ [app/config.py](app/config.py:80-97) - Added backup configuration section

### Database Models
4. ✅ [app/models.py](app/models.py) - Added `Backup` and `BackupRestore` models
5. ✅ [migrations/versions/add_backup_tables.py](migrations/versions/add_backup_tables.py) - Migration for backup tables

### Storage Backend
6. ✅ [app/utils/backup_storage.py](app/utils/backup_storage.py) - B2 storage backend

### Background Workers
7. ✅ [app/workers/__init__.py](app/workers/__init__.py) - RQ setup with Redis connection
8. ✅ [app/workers/backup_jobs.py](app/workers/backup_jobs.py) - Backup job (pg_dump → GPG → B2)
9. ✅ [app/workers/restore_jobs.py](app/workers/restore_jobs.py) - Restore job (B2 → GPG → pg_restore)

### API Routes
10. ✅ [app/routes/admin_backups.py](app/routes/admin_backups.py) - Admin backup API
11. ✅ [app/routes/__init__.py](app/routes/__init__.py:17) - Registered `admin_backups_bp` blueprint

### Scripts
12. ✅ [scripts/run_worker.py](scripts/run_worker.py) - RQ worker startup
13. ✅ [scripts/run_scheduled_backup.py](scripts/run_scheduled_backup.py) - Scheduled backup script
14. ✅ [scripts/cleanup_backups.py](scripts/cleanup_backups.py) - Retention cleanup script

---

## Next Steps (Deployment)

### 1. Run Database Migration

```bash
# Run this to create the backups and backup_restores tables
alembic upgrade head
```

### 2. Set Up Backblaze B2

1. Create a **private** bucket for backups (e.g., `pathsix-backups`)
2. Generate application keys with access to this bucket
3. Note the S3-compatible endpoint URL (e.g., `https://s3.us-west-002.backblazeb2.com`)

### 3. Set Up Redis on Fly.io

```bash
# Create a Redis instance on Fly.io
flyctl redis create

# Note the connection URL (format: redis://default:PASSWORD@HOST:PORT)
```

### 4. Configure Environment Variables

Add these to your Fly.io secrets:

```bash
# Backup storage (Backblaze B2)
flyctl secrets set BACKUP_S3_ENDPOINT_URL="https://s3.us-west-002.backblazeb2.com"
flyctl secrets set BACKUP_S3_REGION="us-west-002"
flyctl secrets set BACKUP_S3_ACCESS_KEY_ID="your-b2-key-id"
flyctl secrets set BACKUP_S3_SECRET_ACCESS_KEY="your-b2-secret-key"
flyctl secrets set BACKUP_S3_BUCKET="pathsix-backups"

# GPG encryption passphrase (IMPORTANT: Keep this safe!)
flyctl secrets set BACKUP_GPG_PASSPHRASE="your-very-secure-passphrase-here"

# Redis connection
flyctl secrets set REDIS_URL="redis://default:PASSWORD@your-redis-host:6379"

# Optional: Adjust retention and timeout
flyctl secrets set BACKUP_RETENTION_DAYS="30"
flyctl secrets set BACKUP_JOB_TIMEOUT_MINUTES="60"
```

### 5. Update fly.toml

Add worker process group:

```toml
[processes]
  app = "hypercorn asgi:app --bind 0.0.0.0:8000"
  worker = "python scripts/run_worker.py"

[[services]]
  processes = ["app"]  # Only expose the app process
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

# Scale the worker process (no external ports)
[processes.worker]
```

### 6. Deploy with Worker Process

```bash
# Deploy with both app and worker processes
flyctl deploy

# Scale worker separately if needed
flyctl scale count worker=1
```

### 7. Set Up Scheduled Backups (Optional)

Create a scheduled machine for daily backups:

```bash
flyctl machines run . \
  --app pathsix-crm-backend \
  --schedule daily \
  --region iad \
  --vm-memory 512 \
  --cmd "python scripts/run_scheduled_backup.py"
```

Create a scheduled machine for weekly cleanup:

```bash
flyctl machines run . \
  --app pathsix-crm-backend \
  --schedule weekly \
  --region iad \
  --vm-memory 256 \
  --cmd "python scripts/cleanup_backups.py"
```

### 8. Test the System

#### Test Manual Backup (via API)

```bash
# Get admin auth token first
TOKEN="your-jwt-token-here"

# Trigger a manual backup
curl -X POST https://your-app.fly.dev/api/admin/backups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# List backups
curl https://your-app.fly.dev/api/admin/backups \
  -H "Authorization: Bearer $TOKEN"

# Get backup status
curl https://your-app.fly.dev/api/admin/backups/1/status \
  -H "Authorization: Bearer $TOKEN"
```

#### Test Restore (DANGER: Destructive)

```bash
# Restore from backup ID 1
# This will automatically create a pre-restore safety backup first
curl -X POST https://your-app.fly.dev/api/admin/backups/1/restore \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

---

## API Endpoints

All endpoints require `admin` role.

### Backups
- `GET /api/admin/backups` - List all backups (with pagination)
- `POST /api/admin/backups` - Trigger manual backup
- `GET /api/admin/backups/:id/status` - Get backup status
- `POST /api/admin/backups/:id/restore` - Restore from backup (creates pre-restore safety backup)
- `DELETE /api/admin/backups/:id` - Delete backup from DB and B2

### Restores
- `GET /api/admin/backups/restores` - List all restore operations

---

## Architecture

### Backup Flow
1. Admin triggers backup via API (or scheduled machine runs)
2. Job creates `Backup` record with status `pending`
3. RQ worker picks up job
4. Worker runs `pg_dump -Fc` → custom format dump
5. Worker encrypts with GPG AES256 (subprocess, passphrase from env)
6. Worker calculates SHA-256 checksum
7. Worker uploads to B2 (storage key: `backups/prod/YYYY/MM/filename`)
8. Worker updates `Backup` record to `completed`
9. Worker cleans up local temp files

### Restore Flow
1. Admin triggers restore via API
2. System creates pre-restore safety backup (automatic)
3. Job waits for safety backup to complete (RQ `depends_on`)
4. Worker downloads encrypted backup from B2
5. Worker verifies SHA-256 checksum
6. Worker decrypts with GPG
7. Worker runs `pg_restore --clean --if-exists`
8. Worker updates `BackupRestore` record to `completed`
9. Worker cleans up local temp files

### File Format
- Dump format: PostgreSQL custom format (`.dump`)
- Encryption: GPG symmetric AES256 (`.gpg`)
- Final filename: `backup_{type}_{timestamp}.dump.gpg`
  - Example: `backup_manual_20251222_143022.dump.gpg`

---

## Security Notes

1. **GPG Passphrase**: Store `BACKUP_GPG_PASSPHRASE` as a Fly.io secret (encrypted at rest)
2. **B2 Bucket**: Use a **private** bucket (not public)
3. **API Access**: All endpoints require `admin` role via JWT
4. **Pre-Restore Backups**: Every restore automatically creates a safety backup first
5. **Checksums**: SHA-256 verification ensures data integrity

---

## Monitoring

### Check Worker Status

```bash
# SSH into Fly.io app
flyctl ssh console

# Check if worker is running
ps aux | grep run_worker
```

### Check Backup Logs

```bash
# View app logs
flyctl logs

# Filter for backup-related logs
flyctl logs --grep "Backup"
flyctl logs --grep "Restore"
```

### Check Redis Queue

```python
# In a Python shell on the worker
from app.workers import backup_queue

# Check queue length
print(f"Jobs in queue: {len(backup_queue)}")

# List jobs
for job in backup_queue.jobs:
    print(f"Job {job.id}: {job.func_name} - {job.get_status()}")
```

---

## Troubleshooting

### Backup Job Stuck in "pending"
- Check if RQ worker process is running
- Check Redis connection (`REDIS_URL`)
- Check worker logs for errors

### GPG Encryption Fails
- Verify `BACKUP_GPG_PASSPHRASE` is set
- Check that `gnupg` is installed in Docker container (it is in Dockerfile)

### B2 Upload Fails
- Verify B2 credentials (`BACKUP_S3_ACCESS_KEY_ID`, `BACKUP_S3_SECRET_ACCESS_KEY`)
- Check bucket name and endpoint URL
- Ensure bucket is in correct region

### pg_dump/pg_restore Fails
- Verify `DATABASE_URL` is correct
- Check that `postgresql-client` is installed (it is in Dockerfile)
- Check database permissions

---

## Cost Estimate (Backblaze B2)

Assuming:
- Database size: 500 MB compressed
- Daily backups with 30-day retention
- 1 restore per month (with pre-restore backup)

**Storage**: 30 backups × 500 MB = 15 GB
- Cost: $0.005/GB/month = **$0.08/month**

**Downloads** (restores): 2 × 500 MB = 1 GB/month
- First 1 GB/day free = **$0.00**

**API Calls**: ~100 calls/month
- Class B (downloads): Free
- Class C (uploads/deletes): 2,500 free/day = **$0.00**

**Total**: ~**$0.08/month** for B2 storage

---

## Future Enhancements (Optional)

- [ ] Email notifications on backup completion/failure
- [ ] Backup size trends dashboard
- [ ] Point-in-time recovery (PITR) with WAL archiving
- [ ] Multi-region backup replication
- [ ] Backup verification jobs (restore to test DB)
- [ ] Frontend UI for backup management

---

## Questions?

Refer to the approved implementation plan in `.claude/plans/generic-whistling-pudding.md` for full implementation details.