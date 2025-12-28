# PathSix CRM Backend - Architecture & API Reference

This document defines the architectural rules, patterns, and API contracts for the PathSix CRM backend.

## Table of Contents

**Part 1: Architecture & Implementation Rules**
1. [Mandatory Implementation Rules](#mandatory-implementation-rules)
2. [High-Level Architecture](#high-level-architecture)
3. [Multi-Tenancy & Security](#multi-tenancy--security)
4. [Status & Validation Strategy](#status--validation-strategy)
5. [Database & Performance](#database--performance)
6. [Development Roadmap](#development-roadmap)
7. [Coding Standards](#coding-standards-for-ai-agents)

**Part 2: API Reference**
8. [Reports API](#reports-api)

---

# Part 1: Architecture & Implementation Rules

## Mandatory Implementation Rules

These rules MUST be followed when making any changes to the codebase.

### Rule 1: Backend Is the Source of Truth for Validation

**Frontend Zod schemas cannot invent or relax rules.**

- **Backend** → Pydantic defines truth
- **Frontend** → Zod mirrors it

This avoids drift, mixed rules, and bugs that only happen on one side.

**Instruction:** For any schema change, update Pydantic first, then Zod to match.

### Rule 2: Backend Must Never Assume a Specific Frontend

Because multiple tenants will hit this backend, the backend must:

- Never assume specific UI components
- Never expect specific enumeration labels from a single frontend
- Never embed any tenant-specific logic

**Instruction:** The backend must remain generic and tenant-agnostic. All tenant overrides happen in frontend config or custom backends, not the shared backend.

### Rule 3: API Responses Must Remain Stable

Since different frontends (versions) may hit the same backend:

- Keep response fields stable
- If you need breaking changes, add versioned endpoints: `/api/v1/...`, `/api/v2/...`

**Instruction:** Validation changes must NOT break the existing response shape unless creating a versioned endpoint.

### Rule 4: Status Values Are Standardized

These status values are SET and will NOT be changed:

```python
PROJECT_STATUS_OPTIONS = ["active", "pending", "completed", "cancelled"]
CLIENT_STATUS_OPTIONS  = ["new", "prospect", "active", "inactive"]
LEAD_STATUS_OPTIONS    = ["new", "contacted", "qualified", "lost", "converted"]
LEAD_SOURCE_OPTIONS    = ["Website", "Referral", "Cold Call", "Email Campaign",
                          "Social Media", "Trade Show", "Advertisement", "Partner", "Other"]
```

**Instruction:** These are the ONLY validated statuses in the generic backend. Custom statuses live in a custom backend later.

### Rule 5: Backend Must Enforce tenant_id Everywhere

You MUST enforce:

- Every query must be scoped by `tenant_id`
- Every insert/update must include `tenant_id`
- Every list view must filter by `tenant_id`

**Instruction:** The backend is multi-tenant by default and must enforce tenant boundaries in every resolver.

### Rule 6: Frontend Must Not Hardcode Backend URLs

Set environment variables:
```bash
VITE_API_URL=http://localhost:5000
```

Then in code:
```javascript
const API_URL = import.meta.env.VITE_API_URL;
```

**Instruction:** All frontends use environment variables for backend URLs so each tenant can point to the right backend instance.

### Rule 7: Validation Must Update Both Front and Back

When doing validation:

1. **Step A** — Define Pydantic schemas
2. **Step B** — Create matching Zod schemas
3. **Step C** — Add runtime backend validation
4. **Step D** — Update frontend forms to use Zod validation

**Instruction:** Validation step must update BOTH front and back. No single-sided validation passes.

### Rule 8: No Tenant-Specific Logic in Generic Backend

If a tenant eventually needs custom statuses, workflows, or fields:

They get:
- Their own backend
- Their own database
- Their own deployment

**Instruction:** The generic backend must stay generic. All "special cases" belong in a dedicated backend.

### Rule 9: Errors Must Be Standardized

Standard error response:
```json
{
  "error": "Invalid lead status",
  "details": { ... }
}
```

**Instruction:** Backend errors must always follow one structure so all frontends can handle them.

### Rule 10: Document All Schemas in Contracts

Keep a `/contracts` folder (future) with all API schema definitions:
```
/contracts
  lead.json
  client.json
  project.json
  user.json
  shared_types.json
```

**Instruction:** This is the canonical handshake between front and back.

---

## High-Level Architecture

### Frontend

- **Stack**: Vite + React + TypeScript
- **Styling**: Tailwind CSS + Catalyst UI (preferred)
  - Shadcn UI / Radix UI allowed only where Catalyst doesn't cover
- **Routing**: React Router
- **Features**: Some views support offline mode + sync

### Backend

- **Framework**: Python + Quart (async Flask-like)
- **Auth**: JWT authentication (email-based login) using Authlib
- **ORM**: SQLAlchemy (migrating away from Flask-specific patterns)
- **Database**: Postgres in production, SQLite in local dev

### Cross-Cutting Concerns

- **Multi-tenant**: Single backend, multiple frontends sharing the instance
- **Tenant field**: `tenant_id` (do not repurpose `client_id`)
- **Entities**: Users, Tenants, Clients, Leads, Projects, Accounts, Contacts, Interactions, Notes
- **Soft delete**: Trash system for Clients, Leads, and Projects

---

## Multi-Tenancy & Security

### Tenancy Rules

**Tenant Model:**
- Every business customer is a tenant
- Each core record includes `tenant_id`
- Queries MUST always filter by `tenant_id`

**Visibility Rules:**

Users see only:
- Leads they created or that are assigned to them
- Clients they created or that are assigned to them

Admins:
- On normal pages: same rule as users (only their own/assigned)
- Separate admin reports can see "all for the tenant" with filters

**Important:** When adding new routes/pages, enforce `tenant_id` filtering and visibility rules.

### Auth & Roles

- **Auth**: JWT-based, login by email
- **Roles**: At least `admin` and `user` roles
- **Routes**: Protected by `@requires_auth` and role checks
- **Future**: User deactivation (`is_active`) instead of hard deletion

**When adding endpoints:**
- Require auth unless it's login/health/public
- Apply role checks for admin-only pages

---

## Status & Validation Strategy

### Standardized Status Fields

Use generic, reusable statuses (see Rule 4). These are enforced via:
- Pydantic models (request validation)
- Zod schemas (frontend validation)

### Validation Plan

- **Frontend**: Zod schemas per entity
- **Backend**: Pydantic models per route input/output

Both sides validate:
- Required fields
- Enum values (statuses)
- Email format, phone formats, etc.

**Keep Zod and Pydantic in sync!**

---

## Database & Performance

### Indexing Strategy

Add indexes on:
- `tenant_id`
- `assigned_to`, `created_by`
- Status fields used in filtering
- `deleted_at` for Trash views
- Any field frequently used in WHERE or ORDER BY

### N+1 Query Avoidance

Use `joinedload` / `selectinload` on relationships:
- `joinedload`: many-to-one (Lead → User)
- `selectinload`: one-to-many (Client → Projects)
- Avoid loading relationships not displayed

### Performance Thresholds

**Database queries:**
- List views: < 200ms
- Detail views: < 100ms
- Search operations: < 500ms
- Bulk operations: < 2s per 100 records

**API endpoints:**
- 95th percentile < 500ms
- Error rate < 1% under normal load
- Support 100+ concurrent tenant users

### Connection Management

**Connection pooling:**
- Pool size: 10-20 connections
- Max overflow: 5 additional
- Connection timeout: 30s
- Pool recycle: 3600s (1 hour)

### Pagination Standards

- Default page size: 25 items
- Maximum page size: 100 items
- Use cursor-based pagination for real-time data
- Include total count only when requested

---

## Development Roadmap

### Phase 1: Validation Standardization ✅ COMPLETE

- ✅ Zod & Pydantic schemas for all entities
- ✅ Generic status options standardized

### Phase 1.5: Monitoring & Visibility ✅ COMPLETE

- ✅ Sentry integration
- ✅ Query logging (slow query detection >200ms)
- ✅ Tenant_id visibility audit

### Phase 2: Code Cleanup & Stability ✅ COMPLETE

- ✅ Database indexes (50+ indexes)
- ✅ N+1 query fixes
- ✅ Security audit (auth endpoints)
- ✅ Error response standardization

### Phase 3: Reports ✅ COMPLETE

- ✅ 10 professional reports implemented
- ✅ Lead source tracking
- ✅ API documentation

### Phase 4: Custom Backends ✅ GUIDELINES ESTABLISHED

- Keep default backend generic
- Custom tenant needs → separate deployments
- No tenant-specific logic in shared codebase

### Phase 4.5: Schema Migration ⏸️ FUTURE

Deferred until multiple customer deployments. Will include:
- API versioning
- Backward compatibility
- Feature flags
- Blue/green deployments

---

## Coding Standards for AI Agents

When modifying this codebase, follow these rules:

### 1. Small, Incremental Changes

Prefer focused edits over broad rewrites.

### 2. Respect Existing Patterns

- For lists + bulk actions: copy patterns from TrashPage and AdminLeadsPage
- For forms: use Catalyst UI components first

### 3. Never Remove Tenant Filtering

Always respect `tenant_id` and visibility rules.

### 4. Keep Auth Flow Intact

Don't re-architect login, tokens, or roles unless explicitly requested.

### 5. Keep Validation Consistent

Update both Zod (frontend) and Pydantic (backend) together.

### 6. No Magic Renames

`tenant_id`, `lead_status`, `client_status` should not be renamed without a migration plan.

### 7. Don't Break Offline Features

Assume offline behavior is important unless told otherwise.

### 8. Add Comments for Non-Obvious Behavior

Especially around visibility rules, business logic, or edge cases.

### 9. Prefer Catalyst + Tailwind Components

Only use Shadcn/Radix when Catalyst doesn't cover the need.

### 10. Testing Requirements

Before committing:
- Test tenant isolation
- Verify visibility rules
- Check auth requirements
- Validate against Pydantic/Zod schemas

---

# Part 2: API Reference

## Reports API

All report endpoints provide business intelligence and analytics for the CRM.

### Common Patterns

**All report endpoints:**
- Located at `/api/reports/*`
- Require authentication (JWT token)
- Support date filtering via `start_date` and `end_date` query parameters
- Return JSON data ready for charts and tables
- Respect tenant isolation automatically

**Query Parameters:**
- `start_date` (optional): ISO date string (e.g., "2024-01-01")
- `end_date` (optional): ISO date string
- `user_id` (optional, admin only): Filter by specific user

---

### 1. Sales Pipeline Report

**Endpoint:** `GET /api/reports/pipeline`

**Purpose:** Tracks leads by stage and value - your front-line health check.

**Response:**
```json
{
  "leads": [
    {"status": "new", "count": 45},
    {"status": "contacted", "count": 23},
    {"status": "qualified", "count": 12},
    {"status": "converted", "count": 8}
  ],
  "projects": [
    {"status": "pending", "count": 15, "total_value": 125000.00},
    {"status": "active", "count": 8, "total_value": 87500.00},
    {"status": "completed", "count": 3, "total_value": 22000.00}
  ]
}
```

**Frontend Usage:**
- Display funnel chart showing lead progression
- Show project pipeline with value totals
- Dashboard overview
- Compare time periods

**Business Value:**
- Daily/weekly pipeline reviews
- Identify bottlenecks in sales process
- Forecast which deals are moving forward
- Team meetings to discuss active opportunities

---

### 2. Lead Source Report

**Endpoint:** `GET /api/reports/lead-source`

**Purpose:** Shows which sources bring in the best leads and highest conversions.

**Response:**
```json
{
  "sources": [
    {
      "source": "Website",
      "total_leads": 120,
      "converted": 15,
      "qualified": 45,
      "conversion_rate": 12.5
    },
    {
      "source": "Referral",
      "total_leads": 85,
      "converted": 22,
      "qualified": 38,
      "conversion_rate": 25.88
    }
  ]
}
```

**Frontend Usage:**
- Bar chart comparing sources by volume
- Highlight best-performing sources (highest conversion_rate)
- ROI analysis for marketing channels
- Table with sortable columns

**Business Value:**
- Marketing ROI analysis
- Budget allocation decisions
- Identify which channels to expand or cut
- Sales team training on what works

**Note:** Requires `lead_source` field on leads.

---

### 3. Conversion Rate Report

**Endpoint:** `GET /api/reports/conversion-rate`

**Purpose:** Measures how well leads move through your funnel and who's closing them.

**Response:**
```json
{
  "overall": {
    "total_leads": 250,
    "converted": 35,
    "conversion_rate": 14.0,
    "avg_days_to_convert": 22.5
  },
  "by_user": [
    {
      "user_email": "john@example.com",
      "total_leads": 50,
      "converted": 12,
      "conversion_rate": 24.0
    }
  ]
}
```

**Frontend Usage:**
- Overall conversion percentage
- Average time to close
- Per-user performance comparison (admin view)

**Business Value:**
- Setting realistic sales goals
- Identifying top performers
- Spotting team members who need coaching
- Benchmarking sales process over time

---

### 4. Revenue by Client Report

**Endpoint:** `GET /api/reports/revenue-by-client`

**Purpose:** Identify top clients by total project value.

**Response:**
```json
{
  "clients": [
    {
      "client_name": "Acme Corp",
      "total_projects": 12,
      "total_value": 450000.00,
      "won_value": 320000.00,
      "pending_value": 130000.00
    }
  ]
}
```

**Frontend Usage:**
- Top clients ranking
- Client value breakdown (won vs pending)
- Account prioritization

**Business Value:**
- Identify high-value relationships
- Account management prioritization
- Revenue concentration analysis

---

### 5. User Activity Report

**Endpoint:** `GET /api/reports/user-activity`

**Purpose:** Tracks team member engagement metrics (admin only).

**Response:**
```json
{
  "users": [
    {
      "user_email": "sales@example.com",
      "assigned_leads": 45,
      "assigned_clients": 23,
      "interactions_logged": 156,
      "projects_created": 8
    }
  ]
}
```

**Frontend Usage:**
- Team performance dashboard
- Workload distribution
- Activity heatmap

**Business Value:**
- Team member engagement tracking
- Workload balancing
- Coaching opportunities

---

### 6. Follow-Up / Inactivity Report

**Endpoint:** `GET /api/reports/follow-ups`

**Purpose:** Highlights overdue follow-ups and inactive contacts.

**Response:**
```json
{
  "overdue_interactions": 12,
  "inactive_clients": [
    {
      "client_name": "Old Corp",
      "days_since_interaction": 90,
      "last_interaction_date": "2024-09-15"
    }
  ],
  "inactive_leads": [...]
}
```

**Frontend Usage:**
- Overdue tasks list
- Re-engagement campaigns
- Priority follow-up queue

**Business Value:**
- Prevent contacts from "going cold"
- Proactive relationship management
- Increase customer retention

---

### 7. Client Retention Report

**Endpoint:** `GET /api/reports/client-retention`

**Purpose:** Shows retention rate and churn.

**Response:**
```json
{
  "retention_rate": 85.5,
  "churn_rate": 14.5,
  "status_breakdown": [
    {"status": "active", "count": 120, "recent_interactions": 89},
    {"status": "inactive", "count": 20, "recent_interactions": 2}
  ]
}
```

**Frontend Usage:**
- Retention/churn metrics
- Status distribution
- Engagement correlation

**Business Value:**
- Track client retention trends
- Identify at-risk accounts
- Measure relationship health

---

### 8. Project Performance Report

**Endpoint:** `GET /api/reports/project-performance`

**Purpose:** Summarizes project outcomes and success rates.

**Response:**
```json
{
  "summary": {
    "total_projects": 150,
    "won": 95,
    "lost": 30,
    "pending": 25,
    "win_rate": 63.3,
    "avg_value": 12500.00,
    "avg_duration_days": 45
  }
}
```

**Frontend Usage:**
- Win rate tracking
- Average project metrics
- Success trend analysis

**Business Value:**
- Sales effectiveness measurement
- Pricing strategy validation
- Process improvement insights

---

### 9. Upcoming Tasks Report

**Endpoint:** `GET /api/reports/upcoming-tasks`

**Purpose:** Lists upcoming meetings, calls, and follow-ups.

**Query Parameters:**
- `days_ahead`: Number of days to look ahead (default: 7)
- `user_id`: Filter by user (admin only)

**Response:**
```json
{
  "tasks": [
    {
      "interaction_type": "meeting",
      "contact_date": "2024-12-30",
      "client_name": "Acme Corp",
      "notes": "Q1 planning meeting"
    }
  ]
}
```

**Frontend Usage:**
- Calendar integration
- Daily task list
- Team schedule view

**Business Value:**
- Never miss a meeting
- Workload planning
- Team coordination

---

### 10. Revenue Forecast Report

**Endpoint:** `GET /api/reports/revenue-forecast`

**Purpose:** Predicts future income with weighted pipeline.

**Response:**
```json
{
  "forecast": {
    "total_pipeline_value": 500000.00,
    "weighted_forecast": 245000.00,
    "won_value": 150000.00,
    "pending_value": 95000.00
  },
  "by_month": [
    {
      "month": "2025-01",
      "weighted_forecast": 85000.00
    }
  ]
}
```

**Weighting:**
- Pending: 30%
- Active: 60%
- Completed/Won: 100%
- Lost/Cancelled: 0%

**Frontend Usage:**
- Revenue projection charts
- Monthly forecast breakdown
- Pipeline confidence scoring

**Business Value:**
- Financial planning
- Resource allocation
- Growth projections

---

## API Response Standards

### Success Response

```json
{
  "data": {...},
  "message": "optional success message"
}
```

### Error Response

```json
{
  "error": "Human-readable error message",
  "details": {
    "field": "Additional context if applicable"
  }
}
```

### Pagination Response

```json
{
  "items": [...],
  "total": 100,
  "limit": 25,
  "offset": 0
}
```

---

## Additional Resources

- **Development Guide**: See [DEV_GUIDE.md](DEV_GUIDE.md)
- **Project Overview**: See [README.md](README.md)
- **Quart Documentation**: https://quart.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/

---

**Last Updated:** December 2024
**Version:** 1.0
