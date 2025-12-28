"""
Decorator for tracking API calls without impacting response time.
"""

from functools import wraps
from quart import request
from app.middleware.usage_tracker import usage_tracker
import asyncio


def track_api_call(fn):
    """
    Decorator to track API calls for quota enforcement.

    This increments the API call counter for the tenant after the response
    is sent, ensuring zero impact on response time.

    Usage:
        @track_api_call
        @requires_auth()
        async def my_endpoint():
            ...
    """
    @wraps(fn)
    async def wrapper(*args, **kwargs):
        # Execute the endpoint
        response = await fn(*args, **kwargs)

        # Track usage asynchronously (non-blocking)
        user = getattr(request, 'user', None)
        if user and hasattr(user, 'tenant_id'):
            # Fire and forget - don't await
            asyncio.create_task(usage_tracker.track_api_call(user.tenant_id))

        return response

    return wrapper
