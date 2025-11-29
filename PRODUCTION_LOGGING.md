# Production Logging Guide

## Viewing Logs in Fly.io Production

### Quick Commands

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

### What You'll See

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

## Long-Term Log Storage (Recommended for Production)

Fly.io logs are temporary. For persistent logs, use a log aggregation service:

### Option 1: Logtail (Recommended - Simple & Cheap)

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

### Option 2: Sentry (Already Configured!)

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

### Option 3: Datadog (Enterprise)

For larger scale:
```bash
fly secrets set LOG_AGGREGATOR=datadog
fly secrets set LOG_AGGREGATOR_TOKEN=your_api_key
```

## Monitoring Strategy

### For Most Cases (Recommended):
1. **Sentry** - Catch all errors and slow requests (already set up!)
2. **Fly logs** - Quick troubleshooting with `fly logs`
3. **Logtail** - If you need to search historical logs

### For Quick Debugging:
```bash
# Watch logs live while testing
fly logs

# In another terminal, make your API calls
curl https://your-app.fly.dev/api/clients/
```

### Alerts to Set Up

In Sentry (already configured):
1. Email on new errors
2. Slack notification on >10 errors/min
3. Weekly performance digest

In Logtail (if you add it):
1. Alert on "Slow query" appearing >5 times/min
2. Alert on ERROR log level
3. Alert on 500 status codes

## Troubleshooting Common Issues

**"I don't see any logs"**
```bash
# Check if app is running
fly status

# Check all instances
fly logs --lines=1000
```

**"Too many logs to read"**
```bash
# Only errors
fly logs --filter="ERROR"

# Only slow queries
fly logs --filter="Slow query"

# Only specific endpoint
fly logs --filter="create_client"
```

**"Logs disappeared after deploy"**
- Normal! Fly.io logs are ephemeral
- Use Logtail or Datadog for persistence

## Cost Breakdown

| Service | Purpose | Cost |
|---------|---------|------|
| Fly.io logs | Quick debugging | Free |
| Sentry | Error tracking | Free tier (5k events/mo) |
| Logtail | Log storage | $10/mo |
| Datadog | Enterprise monitoring | $15/host/mo |

**Recommendation:** Start with Sentry (free) + `fly logs`, add Logtail later if needed.
