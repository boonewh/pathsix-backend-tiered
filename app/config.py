# app/config.py
import os

def _bool(env_name: str, default: bool = False) -> bool:
    return os.getenv(env_name, str(default)).strip().lower() in {"1", "true", "yes", "on"}

def _int(env_name: str, default: int) -> int:
    try:
        return int(os.getenv(env_name, default))
    except (TypeError, ValueError):
        return default
    
# --- Database ---------------------------------------------------------------
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
# Fly.io / Heroku style fix
if raw_db_url.startswith("postgres://"):
    raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

SQLALCHEMY_DATABASE_URI = raw_db_url

# --- App / Security ---------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "rfpikjt7634dvgdihfue7-dev-only")

# Max upload size (bytes) enforced in /api/storage/upload
MAX_CONTENT_LENGTH = _int("MAX_CONTENT_LENGTH", 20 * 1024 * 1024)  # 20 MB default

# Frontend URL used for password reset links, etc.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# --- Mail (SMTP) ------------------------------------------------------------
MAIL_SERVER = os.getenv("MAIL_SERVER", "mail.gandi.net")
MAIL_PORT = _int("MAIL_PORT", 587)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "support@pathsixdesigns.com")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
MAIL_USE_TLS = _bool("MAIL_USE_TLS", True)
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "PathSix CRM")
MAIL_FROM_EMAIL = os.getenv("MAIL_FROM_EMAIL", "support@pathsixdesigns.com")


# --- Error Reporting ---------------------------------------------------------
SENTRY_DSN = os.getenv("SENTRY_DSN", "https://d3a0e864ed57d317f51ff79c95fa1c01@o4509458740609024.ingest.us.sentry.io/4509458747949056")

# --- Logging -----------------------------------------------------------------
# Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Log slow queries (milliseconds threshold)
SLOW_QUERY_THRESHOLD_MS = _int("SLOW_QUERY_THRESHOLD_MS", 200)

# External log aggregation (for production persistence)
# Options: "none", "logtail", "datadog", "papertrail"
LOG_AGGREGATOR = os.getenv("LOG_AGGREGATOR", "none").lower()
LOG_AGGREGATOR_TOKEN = os.getenv("LOG_AGGREGATOR_TOKEN", "")


# --- Storage Backend ---------------------------------------------------------
# Options: "local" or "s3" (works for AWS S3 and S3-compatible providers:
# Backblaze B2, Cloudflare R2, Wasabi, etc.)
STORAGE_VENDOR = os.getenv("STORAGE_VENDOR", "local").lower()

# Local disk (used if STORAGE_VENDOR=local)
STORAGE_ROOT = os.getenv("STORAGE_ROOT", "./storage")

# S3-compatible settings (used if STORAGE_VENDOR=s3)
# Example (Backblaze B2):
#   S3_ENDPOINT_URL=https://s3.us-west-002.backblazeb2.com
#   S3_REGION=us-west-002
#   S3_ACCESS_KEY_ID=xxxxx
#   S3_SECRET_ACCESS_KEY=xxxxx
#   S3_BUCKET=pathsix-vault
#   S3_FORCE_PATH_STYLE=true
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")
S3_REGION = os.getenv("S3_REGION", "")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_FORCE_PATH_STYLE = _bool("S3_FORCE_PATH_STYLE", True)  # prefer path-style for most vendors


# --- Backup Configuration ----------------------------------------------------
# Redis connection for RQ (job queue)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Backup storage (separate B2 bucket)
BACKUP_S3_ENDPOINT_URL = os.getenv("BACKUP_S3_ENDPOINT_URL", "")
BACKUP_S3_REGION = os.getenv("BACKUP_S3_REGION", "us-west-002")
BACKUP_S3_ACCESS_KEY_ID = os.getenv("BACKUP_S3_ACCESS_KEY_ID", "")
BACKUP_S3_SECRET_ACCESS_KEY = os.getenv("BACKUP_S3_SECRET_ACCESS_KEY", "")
BACKUP_S3_BUCKET = os.getenv("BACKUP_S3_BUCKET", "pathsix-backups")

# GPG encryption for backups
BACKUP_GPG_PASSPHRASE = os.getenv("BACKUP_GPG_PASSPHRASE", "")
BACKUP_RETENTION_DAYS = _int("BACKUP_RETENTION_DAYS", 30)

# Backup job timeouts (configurable for large DBs)
BACKUP_JOB_TIMEOUT_MINUTES = _int("BACKUP_JOB_TIMEOUT_MINUTES", 60)  # Default 1 hour


# --- Stripe (Tiered Pricing) ------------------------------------------------
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Stripe Price IDs for each tier (from Stripe Dashboard)
# Create these in Stripe as recurring monthly products
STRIPE_PRICE_STARTER = os.getenv("STRIPE_PRICE_STARTER", "")      # $14.99/mo
STRIPE_PRICE_BUSINESS = os.getenv("STRIPE_PRICE_BUSINESS", "")    # $79/mo
STRIPE_PRICE_ENTERPRISE = os.getenv("STRIPE_PRICE_ENTERPRISE", "")  # $499/mo


# --- (Optional) CORS ---------------------------------------------------------
# For dynamic allow-listing, you can read and parse a CSV of origins here.
# Example:
#   CORS_ALLOWED_ORIGINS="http://localhost:5173,https://pathsix-crm.vercel.app"
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]