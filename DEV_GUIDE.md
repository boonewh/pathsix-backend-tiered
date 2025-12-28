# PathSix CRM Backend - Developer Guide

Complete guide for setting up, running, and maintaining the PathSix CRM backend.

## Table of Contents

1. [Quick Start](#quick-start)
2. [First-Time Setup](#first-time-setup)
3. [Running the Application](#running-the-application)
4. [Common Development Tasks](#common-development-tasks)
5. [Production Logging & Monitoring](#production-logging--monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

For developers who have already set up the project:

```bash
# Activate virtual environment
.\venv\Scripts\activate          # Windows PowerShell
# OR
source venv/bin/activate         # macOS/Linux

# Start dev server
hypercorn asgi:app --bind 0.0.0.0:8000 --reload

# Test it
curl http://localhost:8000/health
```

### Common Commands

```bash
# Start dev server (with auto-reload)
hypercorn asgi:app --bind 0.0.0.0:8000 --reload

# Create admin user
python create_tenant_admin.py

# Reset database (⚠️ destroys all data)
python reset_tables.py

# Seed test data
python seed_all.py

# Database migrations
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "..." # Create new migration
alembic downgrade -1                    # Rollback one migration
```

---

## First-Time Setup

### Prerequisites

- **Python 3.10+** (recommended: 3.11 or 3.12)
- **Git** for version control
- **Redis** (optional - only needed for background jobs/backup testing)

### Installation Steps

#### 1. Clone & Navigate

```bash
cd path/to/pathsix-backend-tiered
```

#### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment

Copy the example environment file:

```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

Edit `.env` and update values as needed. The defaults work for local development with SQLite.

**Key settings for local development:**
- `DATABASE_URL=sqlite:///app.db` (SQLite - no external database needed)
- `STORAGE_VENDOR=local` (Files stored in `./storage` directory)
- `REDIS_URL=redis://localhost:6379/0` (only needed for background jobs)

See [Environment Variables Reference](#environment-variables-reference) for all options.

#### 5. Initialize Database

**Option A: Using the setup script (recommended)**
```bash
python setup_dev.py
```

**Option B: Manual initialization**
```bash
python -c "from app.database import init_db; init_db()"
```

**Option C: Reset everything**
```bash
python reset_tables.py
```

#### 6. Create Admin User

```bash
python create_tenant_admin.py
```

Follow the prompts to create your first admin user.

#### 7. Test the Server

```bash
# Start server
hypercorn asgi:app --bind 0.0.0.0:8000 --reload

# In another terminal, test it
curl http://localhost:8000/health
```

You should see a JSON response confirming the server is running.

---

## Running the Application

### Development Server

**Option A: Using Hypercorn (recommended for Quart)**
```bash
hypercorn asgi:app --bind 0.0.0.0:8000 --reload
```

**Option B: Using Quart's built-in server**
```bash
quart --app asgi:app run --port 8000
```

The API will be available at: `http://localhost:8000`

### Default Configuration

- **Database**: SQLite (`app.db`)
- **Storage**: Local (`./storage/`)
- **Frontend**: http://localhost:5173
- **Port**: 8000

---

## Common Development Tasks

### Database Migrations

**Create a new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback one migration:**
```bash
alembic downgrade -1
```

**Check current migration:**
```bash
alembic current
```

### Seeding Test Data

```bash
# Seed everything
python seed_all.py

# Seed specific data
python seed_roles.py
```

### Running Tests

```bash
pytest
```

### Linting & Formatting

```bash
# Install dev dependencies
pip install black flake8 mypy

# Format code
black .

# Lint
flake8 app/

# Type checking
mypy app/
```

### Working with Git

```bash
# See modified files
git status

# View changes
git diff

# Stage and commit
git add .
git commit -m "Your commit message"

# Push to remote
git push
```

---

## Production Logging & Monitoring

### Viewing Logs in Fly.io Production

#### Quick Commands

```bash
# Real-time logs (live tail)
fly logs

# Filter for warnings and errors only
fly logs --filter="WARNING|ERROR"

# Show slow queries
fly logs --filter="Slow query"

# Last 500 lines
fly logs --lines=500

# Specific app (if you have multiple)
fly logs -a pathsix-backend
```

#### What You'll See

**Normal Request:**
```
2025-11-29 10:15:23 [INFO] pathsix - Endpoint completed: {'endpoint': 'clients.list_clients', 'duration_ms': 45.32, 'status_code': 200, 'tenant_id': 1}
```

**Slow Query Warning:**
```
2025-11-29 10:15:24 [WARNING] sqlalchemy.queries - Slow query detected (245.67ms): SELECT clients.id FROM clients WHERE...
```

**Error:**
```
2025-11-29 10:15:25 [ERROR] pathsix - Error occurred: {'error_type': 'ValidationError', 'context': 'Invalid client data', 'tenant_id': 1}
```

### Long-Term Log Storage

Fly.io logs are temporary. For persistent logs, use a log aggregation service:

#### Option 1: Logtail (Recommended - Simple & Cheap)

1. Sign up at https://betterstack.com/logtail
2. Get your source token
3. Add to Fly.io secrets:
   ```bash
   fly secrets set LOG_AGGREGATOR=logtail
   fly secrets set LOG_AGGREGATOR_TOKEN=your_token_here
   ```
4. View logs at betterstack.com dashboard

**Benefits:**
- 7-14 day retention
- Search and filtering
- $10/month for small apps
- Alerts on errors

#### Option 2: Sentry (Already Configured!)

**For Errors Only:**
- Go to https://sentry.io
- View your `pathsix-backend` project
- See errors, slow transactions, and performance data

**What Sentry Shows:**
- ✅ All Python exceptions with stack traces
- ✅ Slow API endpoints (>500ms)
- ✅ Which tenant/user experienced the error
- ✅ Frequency and trends
- ⚠️ Does NOT show normal INFO logs (only errors)

#### Option 3: Datadog (Enterprise)

For larger scale:
```bash
fly secrets set LOG_AGGREGATOR=datadog
fly secrets set LOG_AGGREGATOR_TOKEN=your_api_key
```

### Monitoring Strategy

**For Most Cases (Recommended):**
1. **Sentry** - Catch all errors and slow requests (already set up!)
2. **Fly logs** - Quick troubleshooting with `fly logs`
3. **Logtail** - If you need to search historical logs

**For Quick Debugging:**
```bash
# Watch logs live while testing
fly logs

# In another terminal, make your API calls
curl https://your-app.fly.dev/api/clients/
```

### Alerts to Set Up

**In Sentry (already configured):**
1. Email on new errors
2. Slack notification on >10 errors/min
3. Weekly performance digest

**In Logtail (if you add it):**
1. Alert on "Slow query" appearing >5 times/min
2. Alert on ERROR log level
3. Alert on 500 status codes

### Cost Breakdown

| Service | Purpose | Cost |
|---------|---------|------|
| Fly.io logs | Quick debugging | Free |
| Sentry | Error tracking | Free tier (5k events/mo) |
| Logtail | Log storage | $10/mo |
| Datadog | Enterprise monitoring | $15/host/mo |

**Recommendation:** Start with Sentry (free) + `fly logs`, add Logtail later if needed.

---

## Troubleshooting

### Port Already in Use

If port 8000 is already taken, change the `PORT` in `.env` or run:

```bash
hypercorn asgi:app --bind 0.0.0.0:8080
```

### Database Locked (SQLite)

SQLite doesn't handle concurrent writes well. If you see "database is locked" errors:

1. Close any other processes accessing the database
2. Use PostgreSQL instead for better concurrency
3. Reduce simultaneous requests

### ModuleNotFoundError

Make sure your virtual environment is activated:

```bash
# Check if venv is active (should see (venv) in prompt)
which python  # macOS/Linux
where python  # Windows
```

### Redis Connection Error

If you're not using background jobs, Redis isn't required. The error can be safely ignored.

To fix it, either:
1. Install and run Redis locally
2. Comment out Redis-dependent code (check `app/workers/__init__.py`)

### "I don't see any logs" (Production)

```bash
# Check if app is running
fly status

# Check all instances
fly logs --lines=1000
```

### "Too many logs to read" (Production)

```bash
# Only errors
fly logs --filter="ERROR"

# Only slow queries
fly logs --filter="Slow query"

# Only specific endpoint
fly logs --filter="create_client"
```

### "Logs disappeared after deploy" (Production)

- Normal! Fly.io logs are ephemeral
- Use Logtail or Datadog for persistence

---

## Auto-Backup System (Safe for Development)

The auto-backup system **will NOT run automatically** in your local development environment.

### Why It Won't Run in Development

1. **Scheduled Execution**: The backup system runs on a Fly.io scheduled machine (cron-like) that executes `scripts/run_scheduled_backup.py` daily at 2 AM UTC in production.

2. **Manual Trigger Only**: In development, backups can only be triggered manually through the API or by running scripts directly.

3. **PostgreSQL Required**: The backup script explicitly checks for PostgreSQL and will error if you're using SQLite (which is the default for local dev).

4. **Redis Queue**: Background backup jobs use Redis queues, which won't be available unless you specifically set up and run Redis locally.

### If You Want to Test Backups Locally

1. Install PostgreSQL and Redis
2. Update `DATABASE_URL` in `.env` to point to your local PostgreSQL
3. Update `REDIS_URL` in `.env` to point to your local Redis
4. Configure backup S3 credentials in `.env`
5. Run the Redis worker: `python scripts/run_worker.py`
6. Manually trigger a backup via the API or CLI

### Backup-Related Files (for reference)

- `scripts/run_scheduled_backup.py` - Scheduled backup entry point (Fly.io only)
- `app/workers/backup_jobs.py` - Backup job logic (pg_dump + GPG + B2 upload)
- `app/routes/admin_backups.py` - API endpoints for manual backup management
- `setup_scheduled_backup.sh` - Fly.io scheduled machine setup script

**You can safely ignore these files during normal development.**

---

## Project Structure

```
pathsix-backend-tiered/
├── app/
│   ├── __init__.py          # Quart app factory
│   ├── config.py            # Configuration loader from .env
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Database models
│   ├── routes/              # API route blueprints
│   ├── utils/               # Utility functions
│   └── workers/             # Background job handlers (RQ)
├── migrations/              # Alembic database migrations
├── scripts/                 # Utility scripts (backup, worker, etc.)
├── asgi.py                  # ASGI entry point
├── requirements.txt         # Python dependencies
├── .env                     # Your local environment config (not in git)
├── .env.example             # Template for .env
└── DEV_GUIDE.md            # This file
```

---

## Environment Variables Reference

See `.env.example` for a complete list of configuration options.

### Critical Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///app.db` | Database connection string |
| `SECRET_KEY` | (dev key) | Flask session signing key |
| `FRONTEND_URL` | `http://localhost:5173` | Frontend URL for CORS and email links |
| `STORAGE_VENDOR` | `local` | Storage backend: `local` or `s3` |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection for background jobs |

### Optional Variables

- **Email**: `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`, etc.
- **Error Tracking**: `SENTRY_DSN`
- **Logging**: `LOG_LEVEL`, `LOG_AGGREGATOR`
- **Backups**: `BACKUP_S3_*`, `BACKUP_GPG_PASSPHRASE`

---

## Tech Stack

- **Framework**: Quart (async Flask-like framework)
- **Database**: SQLAlchemy 2.0 (with async support)
- **Queue**: RQ (Redis Queue) for background jobs
- **Server**: Hypercorn (ASGI server)
- **Storage**: Local filesystem or S3-compatible (Backblaze B2)
- **Email**: aiosmtplib (async SMTP)
- **Migrations**: Alembic

---

## Deployment

This backend is designed to run on Fly.io, but can be deployed anywhere that supports Python ASGI apps.

### Fly.io Deployment

```bash
# Install flyctl
# https://fly.io/docs/hands-on/install-flyctl/

# Login
flyctl auth login

# Deploy
flyctl deploy
```

### Docker Deployment

```bash
# Build
docker build -t pathsix-backend .

# Run
docker run -p 8000:8000 --env-file .env pathsix-backend
```

---

## Additional Resources

- **Architecture & Rules**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Project Overview**: See [README.md](README.md)
- **Quart Documentation**: https://quart.palletsprojects.com/

---

## Next Steps

1. Set up your `.env` file
2. Initialize the database
3. Create an admin user
4. Start the dev server
5. Connect your frontend (default: http://localhost:5173)
6. Start building!

Happy coding!
