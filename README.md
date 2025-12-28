# PathSix CRM Backend

A Quart-based (async Flask) backend for the PathSix CRM system.

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

# 4. Run setup script (creates DB, optionally creates admin user)
python setup_dev.py
```

### Running the Application

```bash
# Make sure virtual environment is activated
hypercorn asgi:app --bind 0.0.0.0:8000 --reload
```

The server will start on `http://localhost:8000`

## Documentation

- **[DEV_GUIDE.md](DEV_GUIDE.md)** - Complete development guide (setup, troubleshooting, production logging)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Architecture rules, patterns, and API reference
- **[.env.example](.env.example)** - Environment variable template

## Environment Configuration

The application uses the following default configuration for local development:

- **Database**: SQLite (`app.db`)
- **Port**: 8000
- **Storage**: Local filesystem (`./storage`)
- **Frontend URL**: http://localhost:5173

## Tech Stack

- **Framework**: Quart (async Flask-like framework)
- **Database**: SQLAlchemy 2.0 with SQLite (dev) / PostgreSQL (production)
- **Queue**: RQ (Redis Queue) for background jobs
- **Server**: Hypercorn (ASGI server)
- **Storage**: Local filesystem or S3-compatible (Backblaze B2)
- **Email**: aiosmtplib (async SMTP)
- **Migrations**: Alembic

## API Features

- **Authentication**: JWT-based authentication
- **Multi-tenant**: Support for multiple tenants with strict isolation
- **CRUD Operations**: For clients, projects, leads, contacts, interactions
- **File Storage**: Local and S3-compatible storage
- **Email**: SMTP email sending
- **Search**: Global search across entities
- **Reports**: 10 comprehensive business intelligence reports

## Project Structure

```
app/
├── __init__.py          # App factory and configuration
├── config.py           # Configuration settings
├── database.py         # Database connection and session
├── models.py           # SQLAlchemy models
├── routes/             # API endpoints
│   ├── auth.py         # Authentication
│   ├── clients.py      # Client management
│   ├── leads.py        # Lead management
│   ├── projects.py     # Project management
│   ├── reports.py      # Business intelligence reports
│   └── ...
└── utils/              # Utility functions
    ├── auth_utils.py   # Authentication helpers
    ├── email_utils.py  # Email utilities
    └── ...
```

## Development Notes

- Uses Quart (async Flask) for better performance
- SQLAlchemy ORM with SQLite for local development
- CORS configured for frontend integration
- Background tasks for database keep-alive
- Structured logging with slow query detection
- Sentry integration for error tracking

## Production Deployment

Designed for Fly.io, but can run anywhere that supports Python ASGI apps.

**Production Checklist:**
- PostgreSQL instead of SQLite
- Hypercorn or Uvicorn as ASGI server
- Environment variables for sensitive configuration
- S3-compatible storage for file uploads
- Redis for background jobs
- Proper SMTP configuration for emails
- Log aggregation (Logtail or Datadog)
- Error tracking (Sentry - already configured)

See [DEV_GUIDE.md](DEV_GUIDE.md#deployment) for deployment instructions.

## Contributing

Before making changes, read:
1. [ARCHITECTURE.md](ARCHITECTURE.md) - Implementation rules and patterns
2. [DEV_GUIDE.md](DEV_GUIDE.md) - Development workflow

## License

Proprietary - PathSix Solutions
