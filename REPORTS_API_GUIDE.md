# Reports API - Frontend Integration Guide

This document describes all 10 reporting endpoints and how to integrate them in your frontend.

## Overview

All report endpoints:
- Are located at `/api/reports/*`
- Require authentication (JWT token)
- Support date filtering via `start_date` and `end_date` query parameters
- Return JSON data ready for charts and tables
- Respect tenant isolation automatically

---

## 1. Sales Pipeline Report

**Endpoint:** `GET /api/reports/pipeline`

**Purpose:** Tracks leads by stage and value - your front-line health check.

**Query Parameters:**
- `start_date` (optional): ISO date string (e.g., "2024-01-01")
- `end_date` (optional): ISO date string
- `user_id` (optional, admin only): Filter by specific user

**Response:**
```json
{
  "leads": [
    {"status": "open", "count": 45},
    {"status": "qualified", "count": 23},
    {"status": "proposal", "count": 12},
    {"status": "closed", "count": 8}
  ],
  "projects": [
    {"status": "pending", "count": 15, "total_value": 125000.00},
    {"status": "won", "count": 8, "total_value": 87500.00},
    {"status": "lost", "count": 3, "total_value": 22000.00}
  ]
}
```

**Frontend Usage:**
- Display funnel chart showing lead progression
- Show project pipeline with value totals
- Use for dashboard overview
- Compare time periods with date filters

---

## 2. Lead Source Report

**Endpoint:** `GET /api/reports/lead-source`

**Purpose:** Shows which sources bring in the best leads and highest conversions.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

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

**Note:** Requires `lead_source` field on leads. Run migration first!

---

## 3. Conversion Rate Report

**Endpoint:** `GET /api/reports/conversion-rate`

**Purpose:** Measures how well leads move through your funnel and who's closing them.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
  "overall": {
    "total_leads": 250,
    "converted_leads": 42,
    "conversion_rate": 16.8,
    "avg_days_to_convert": 18.5
  },
  "by_user": [
    {
      "user_id": 5,
      "user_email": "john@example.com",
      "total_leads": 80,
      "converted": 18,
      "conversion_rate": 22.5
    }
  ]
}
```

**Frontend Usage:**
- Gauge/percentage display for overall rate
- Leaderboard showing top performers
- Time-to-conversion metric
- Team performance comparison table
- Admin view only shows `by_user` data

---

## 4. Revenue by Client Report

**Endpoint:** `GET /api/reports/revenue-by-client`

**Purpose:** Aggregates all project totals per client - shows high-value clients.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)
- `limit` (optional, default: 50): Number of clients to return

**Response:**
```json
{
  "clients": [
    {
      "client_id": 12,
      "client_name": "Acme Corp",
      "project_count": 8,
      "won_value": 450000.00,
      "pending_value": 125000.00,
      "total_value": 575000.00
    }
  ]
}
```

**Frontend Usage:**
- Top clients table (sorted by total_value)
- Revenue breakdown chart
- Client lifetime value analysis
- Click client to view details

---

## 5. User Activity Report

**Endpoint:** `GET /api/reports/user-activity`

**Purpose:** Tracks each team member's engagement. **Admin only.**

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
  "users": [
    {
      "user_id": 5,
      "email": "john@example.com",
      "interactions": 142,
      "leads_assigned": 35,
      "clients_assigned": 18,
      "activity_count": 287
    }
  ]
}
```

**Frontend Usage:**
- Team activity dashboard
- Performance metrics per user
- Workload distribution view
- Identify inactive users

---

## 6. Follow-Up / Inactivity Report

**Endpoint:** `GET /api/reports/follow-ups`

**Purpose:** Highlights contacts overdue for outreach or with no recent activity.

**Query Parameters:**
- `inactive_days` (optional, default: 30): Threshold for inactivity

**Response:**
```json
{
  "overdue_follow_ups": [
    {
      "interaction_id": 234,
      "client_id": 15,
      "lead_id": null,
      "entity_name": "Acme Corp",
      "follow_up_date": "2024-11-15T14:00:00Z",
      "summary": "Follow up on proposal",
      "days_overdue": 5
    }
  ],
  "inactive_clients": [
    {
      "client_id": 22,
      "name": "Beta Industries",
      "last_interaction": "2024-10-01T10:00:00Z",
      "days_inactive": 45
    }
  ],
  "inactive_leads": [
    {
      "lead_id": 78,
      "name": "Gamma Solutions",
      "last_interaction": "2024-09-20T15:00:00Z",
      "days_inactive": 52
    }
  ]
}
```

**Frontend Usage:**
- Alert/notification style display for overdue items
- "At Risk" clients dashboard
- Sort by days_overdue/days_inactive
- Quick action buttons (call, email, schedule)

---

## 7. Client Retention / Churn Report

**Endpoint:** `GET /api/reports/client-retention`

**Purpose:** Shows how many clients renewed, stayed active, or dropped off over time.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
  "status_breakdown": [
    {"status": "new", "count": 25},
    {"status": "active", "count": 142},
    {"status": "inactive", "count": 18}
  ],
  "total_active": 167,
  "churned": 8,
  "active_with_recent_interactions": 98,
  "retention_rate": 95.43
}
```

**Frontend Usage:**
- Donut chart for status breakdown
- Retention rate KPI display
- Churn trend over time (compare periods)
- Health score indicator

---

## 8. Project Performance Report

**Endpoint:** `GET /api/reports/project-performance`

**Purpose:** Summarizes project outcomes, durations, or success rates.

**Query Parameters:**
- `start_date` (optional)
- `end_date` (optional)

**Response:**
```json
{
  "status_breakdown": [
    {"status": "pending", "count": 15, "total_value": 225000.00},
    {"status": "won", "count": 28, "total_value": 510000.00},
    {"status": "lost", "count": 7, "total_value": 85000.00}
  ],
  "total_projects": 50,
  "win_rate": 56.00,
  "avg_duration_days": 45.3,
  "avg_project_value": 16400.00
}
```

**Frontend Usage:**
- Win rate gauge/percentage
- Project value distribution chart
- Duration metrics for planning
- Success indicators

---

## 9. Upcoming Tasks & Appointments Report

**Endpoint:** `GET /api/reports/upcoming-tasks`

**Purpose:** Lists upcoming meetings, calls, or follow-ups for the team.

**Query Parameters:**
- `days` (optional, default: 30): How many days ahead to look
- `user_id` (optional, admin only): Filter by specific user

**Response:**
```json
{
  "upcoming_tasks": [
    {
      "interaction_id": 456,
      "client_id": 12,
      "lead_id": null,
      "entity_name": "Acme Corp",
      "follow_up_date": "2024-11-25T10:00:00Z",
      "summary": "Product demo call",
      "status": "pending",
      "days_until": 3,
      "assigned_to": "john@example.com"
    }
  ]
}
```

**Frontend Usage:**
- Calendar view of upcoming tasks
- Daily/weekly task list
- Grouped by days_until
- Assign colors by status
- Filter by assigned user

---

## 10. Revenue Forecast Report

**Endpoint:** `GET /api/reports/revenue-forecast`

**Purpose:** Predicts likely future income based on weighted pipeline stages.

**Query Parameters:** None

**Response:**
```json
{
  "projects": [
    {
      "status": "pending",
      "count": 15,
      "total_value": 225000.00,
      "weighted_value": 67500.00,
      "weight": 0.3
    },
    {
      "status": "won",
      "count": 28,
      "total_value": 510000.00,
      "weighted_value": 510000.00,
      "weight": 1.0
    }
  ],
  "total_weighted_forecast": 577500.00,
  "lead_pipeline": [
    {"status": "open", "count": 45},
    {"status": "qualified", "count": 23}
  ]
}
```

**Frontend Usage:**
- Total forecast as main KPI
- Breakdown by status with weights
- Explain weighting to users (pending = 30% likely)
- Compare to historical revenue
- Lead pipeline context

**Weighting Logic:**
- `pending`: 30% (3 out of 10 close)
- `won`: 100% (already closed)
- `lost`: 0% (not happening)

---

## Common Frontend Patterns

### Date Range Picker
```javascript
const [startDate, setStartDate] = useState(null);
const [endDate, setEndDate] = useState(null);

const fetchReport = async () => {
  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate.toISOString().split('T')[0]);
  if (endDate) params.append('end_date', endDate.toISOString().split('T')[0]);
  
  const response = await fetch(`/api/reports/pipeline?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

### Chart Libraries
Recommended: **Recharts** or **Chart.js**

Example with Recharts:
```jsx
import { BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

<BarChart data={report.sources}>
  <XAxis dataKey="source" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="total_leads" fill="#8884d8" />
  <Bar dataKey="converted" fill="#82ca9d" />
</BarChart>
```

### CSV Export
```javascript
const exportToCSV = (data, filename) => {
  const csv = Papa.unparse(data); // using papaparse library
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
};
```

---

## Authentication

All endpoints require JWT authentication:

```javascript
const headers = {
  'Authorization': `Bearer ${yourJWTToken}`,
  'Content-Type': 'application/json'
};
```

---

## Admin vs User Access

**Admin Only:**
- User Activity Report (`/user-activity`)

**Admin Features:**
- Sales Pipeline: Can filter by `user_id`
- Conversion Rate: Sees `by_user` breakdown
- Upcoming Tasks: Can filter by `user_id`

**All Users:**
- All other endpoints (filtered to their assigned entities)

---

## Error Handling

All endpoints return standard error format:

```json
{
  "error": "Error message here"
}
```

Common HTTP Status Codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (admin-only endpoint)
- `500`: Server error

---

## Migration Required

Before using the Lead Source Report (#2), you must run the database migration:

```bash
# Apply the migration
alembic upgrade head
```

This adds the `lead_source` column to the `leads` table.

---

## Next Steps

1. **Create Report Pages** - Build React components for each report
2. **Add Navigation** - Include reports in your sidebar menu
3. **Build Dashboard** - Combine key metrics from multiple reports
4. **Export Features** - Add CSV/PDF export buttons
5. **Scheduled Reports** - Email reports on schedule (future feature)

---

## Support

For questions or issues with these endpoints, refer to:
- Backend code: `app/routes/reports.py`
- Database models: `app/models.py`
- Constants: `app/constants.py` (for valid lead sources)
