# PathSix CRM Backend - Tiered Pricing Edition

A production-ready Quart-based (async Flask) backend for the PathSix CRM system with **multi-tenant tiered pricing**, **Stripe billing integration**, and **hard quota enforcement**.

## Features

### Core CRM Features
- **Authentication**: JWT-based with email verification
- **Multi-tenant**: Strict tenant isolation with data scoping
- **CRUD Operations**: Clients, projects, leads, contacts, interactions
- **File Storage**: Local and S3-compatible (Backblaze B2)
- **Search**: Global search across entities
- **Reports**: 10 comprehensive business intelligence reports

### Tiered Pricing System
- **4 Pricing Tiers**: Free, Starter ($14.99/mo), Business ($79/mo), Enterprise ($499/mo)
- **Hard Quota Enforcement**: Records, storage, users, API calls, emails per month
- **Stripe Integration**: Automated subscription management, customer portal, webhooks
- **Email Verification**: Required for all signups to prevent spam
- **Usage Tracking**: Real-time quota monitoring with batch processing
- **Upgrade Flows**: Seamless tier upgrades via Stripe Checkout

### Quota Limits by Tier

| Feature | Free | Starter | Business | Enterprise |
|---------|------|---------|----------|------------|
| **Price** | $0 | $14.99/mo | $79/mo | $499/mo |
| **Users** | 1 | 3 | 10 | Unlimited |
| **Storage** | 0 GB | 2 GB | 25 GB | 250 GB |
| **Records** | 25 | 5,000 | 50,000 | 500,000 |
| **API Calls/Day** | 100 | 5,000 | 50,000 | Unlimited |
| **Emails/Month** | 3 | 100 | 1,000 | 10,000 |
| **File Uploads** | ❌ | ✅ | ✅ | ✅ |

## Quick Setup

### Automated Setup (Recommended)

```bash
# 1. Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
copy .env.example .env  # Windows
# OR
cp .env.example .env    # macOS/Linux

# 4. Initialize database with roles, plans, and test admin
python setup_database.py
```

### Running the Application

```bash
# Make sure virtual environment is activated
python run.py

# Server starts on http://localhost:8000
```

### Test Login Credentials

After running `setup_database.py`, you'll have:

```
Email: admin@pathsix.local
Password: PathSix2025!
Plan: Enterprise (for testing without quota limits)
```

## Documentation

- **[DEV_GUIDE.md](DEV_GUIDE.md)** - Complete development guide (setup, troubleshooting, production)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture rules, patterns, and API reference
- **[PWA_IMPLEMENTATION_GUIDE.md](PWA_IMPLEMENTATION_GUIDE.md)** - Progressive Web App implementation guide
- **[.env.example](.env.example)** - Environment variable template

## API Endpoints

### Authentication
- `POST /api/signup` - Create new tenant and user with email verification
- `POST /api/verify-email/<token>` - Verify email and auto-login
- `POST /api/resend-verification` - Resend verification email
- `POST /api/login` - Login (requires verified email)
- `POST /api/forgot-password` - Request password reset
- `POST /api/reset-password/<token>` - Reset password

### Billing & Usage
- `GET /api/billing/usage` - Current usage and quota limits
- `GET /api/billing/plan` - Current plan details
- `POST /api/billing/create-checkout-session` - Initiate Stripe checkout for upgrade
- `POST /api/billing/customer-portal` - Get Stripe customer portal link
- `POST /api/webhooks/stripe` - Stripe webhook handler (subscription lifecycle)

### Admin Analytics (Platform Owner Only - NOT for Tenants)
**IMPORTANT:** These endpoints are for YOU (the SaaS platform owner), not your customers. They provide visibility into ALL tenants, revenue metrics, and business health across your entire platform.

**Access:** Requires `admin` role (only platform owner account has this)

Admin-only endpoints for platform visibility and business metrics:
- `GET /api/admin/analytics/overview` - Platform overview (total tenants, MRR, signups)
- `GET /api/admin/analytics/tiers` - Breakdown by pricing tier
- `GET /api/admin/analytics/usage` - Customers approaching quota limits
- `GET /api/admin/analytics/customers` - Customer list with filters (tier, status, sort, pagination)
- `GET /api/admin/analytics/revenue` - Revenue metrics (MRR, churn, LTV, trends)
- `GET /api/admin/analytics/health` - Platform health (failed payments, upsell opportunities)

**Note:** Regular tenant users signing up through `/api/signup` do NOT get admin role and cannot access these endpoints. This is completely separate from tenant CRM functionality.

### CRM Endpoints
All CRM endpoints require authentication and enforce quota limits:
- `/api/clients/*` - Client management
- `/api/leads/*` - Lead management
- `/api/projects/*` - Project management
- `/api/contacts/*` - Contact management
- `/api/interactions/*` - Interaction tracking
- `/api/storage/*` - File upload/download (quota enforced)
- `/api/users/*` - User management (max users per tier)
- `/api/reports/*` - Business intelligence reports

## Environment Configuration

### Required for Development

```bash
DATABASE_URL=sqlite:///app.db
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
FRONTEND_URL=http://localhost:5173
```

### Required for Production (Stripe)

```bash
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_STARTER=price_...  # Stripe Price ID for $14.99/mo
STRIPE_PRICE_BUSINESS=price_... # Stripe Price ID for $79/mo
STRIPE_PRICE_ENTERPRISE=price_... # Stripe Price ID for $499/mo
```

### Optional (Email Verification)

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

See [.env.example](.env.example) for complete configuration options.

## Tech Stack

- **Framework**: Quart (async Flask-like framework)
- **Database**: SQLAlchemy 2.0 with SQLite (dev) / PostgreSQL (production)
- **Payments**: Stripe (subscriptions, billing, webhooks)
- **Email**: aiosmtplib (async SMTP)
- **Storage**: Local filesystem or S3-compatible (Backblaze B2)
- **Queue**: RQ (Redis Queue) for background jobs
- **Server**: Hypercorn (ASGI server)
- **Migrations**: Alembic

## Project Structure

```
app/
├── __init__.py          # App factory and configuration
├── config.py           # Configuration settings
├── database.py         # Database connection and session
├── models.py           # SQLAlchemy models (Tenant, User, PlanLimit, etc.)
├── routes/             # API endpoints
│   ├── auth.py         # Authentication (signup, verify, login)
│   ├── billing.py      # Usage tracking and Stripe checkout
│   ├── webhooks.py     # Stripe webhook handlers
│   ├── clients.py      # Client management (quota enforced)
│   ├── leads.py        # Lead management (quota enforced)
│   ├── storage.py      # File uploads (quota enforced)
│   ├── users.py        # User management (max users enforced)
│   └── ...
├── middleware/         # Request middleware
│   └── quota_enforcer.py # Pre-flight quota checks
└── utils/              # Utility functions
    ├── auth_utils.py   # Authentication helpers
    ├── email_utils.py  # Email sending
    ├── quota_helpers.py # Quota checking logic
    └── ...
```

## Security Features

- ✅ **JWT Authentication** - Required on all CRM endpoints
- ✅ **Email Verification** - Blocks unverified users from login
- ✅ **Tenant Isolation** - Complete data scoping by tenant_id
- ✅ **Rate Limiting** - Login (5/min), signup (3/5min), password reset (3/5min)
- ✅ **Role-Based Access** - Admin and file_uploads roles
- ✅ **Stripe Webhook Verification** - Signature validation on all webhooks
- ✅ **Password Hashing** - Bcrypt with salt
- ✅ **CORS Protection** - Configurable allowed origins

## Quota Enforcement

### How It Works

1. **Pre-flight Checks**: Middleware checks quotas BEFORE write operations
2. **Hard Limits**: Operations blocked at quota limit (no soft warnings)
3. **Read-Only Mode**: When quota exceeded, GET requests allowed, POST/PUT/DELETE blocked
4. **Cost Protection**: Prevents free/low-tier users from accumulating massive costs

### Quota Error Response

```json
{
  "error": "Storage limit reached. Your starter plan allows 2 GB. Please upgrade your plan.",
  "quota_type": "storage",
  "current": 2147483648,
  "limit": 2147483648,
  "upgrade_url": "/billing"
}
```

HTTP Status: `403 Forbidden`

## Production Deployment

### Checklist

**Database:**
- [ ] PostgreSQL instead of SQLite
- [ ] Run `python setup_database.py` on production database
- [ ] Connection pooling configured

**Stripe:**
- [ ] Create 3 products in Stripe (Starter, Business, Enterprise)
- [ ] Set environment variables for price IDs
- [ ] Set up webhook endpoint in Stripe dashboard
- [ ] Test webhook with Stripe CLI

**Email:**
- [ ] Production SMTP credentials configured
- [ ] Test signup email verification flow

**Security:**
- [ ] HTTPS enabled on API domain
- [ ] CORS configured for frontend domain only
- [ ] Environment variables secured (not in code)
- [ ] Database credentials rotated

**Monitoring:**
- [ ] Sentry configured for error tracking
- [ ] Log aggregation (Logtail or Datadog)
- [ ] Uptime monitoring

See [DEV_GUIDE.md](DEV_GUIDE.md#deployment) for detailed deployment instructions.

## Development Notes

- Uses Quart (async Flask) for better performance
- SQLAlchemy ORM with async support
- CORS configured for frontend integration
- Structured logging with slow query detection (>200ms)
- Sentry integration for error tracking
- Background tasks for usage tracking (5-second batches)

## Testing the Tiered Pricing System

### 1. Test Free Tier Limits

```bash
# Login as admin (starts on enterprise, downgrade to free for testing)
# Try to create 101st record - should fail with quota error
# Try to add 2nd user - should fail with user limit error
```

### 2. Test Signup Flow

```bash
curl -X POST http://localhost:8000/api/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","company_name":"Test Corp"}'

# Check server console for verification link
# Click link to verify email
# Login should now work
```

### 3. Test Usage Dashboard

```bash
# Get current usage and limits
curl http://localhost:8000/api/billing/usage \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Test Stripe Checkout (Requires Stripe Config)

```bash
# Create checkout session for Starter plan
curl -X POST http://localhost:8000/api/billing/create-checkout-session \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tier":"starter"}'
```

## Common Commands

```bash
# Start dev server (with auto-reload)
python run.py

# Initialize/reset database
python setup_database.py

# Create migrations
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# View all registered routes
python test_routes.py
```

## Contributing

Before making changes, read:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Implementation rules and patterns
2. [DEV_GUIDE.md](DEV_GUIDE.md) - Development workflow

## License

Proprietary - PathSix Solutions

---

**Status:** Production-ready for SaaS deployment
**Last Updated:** January 2026
**Version:** 2.0 (Tiered Pricing Edition)
