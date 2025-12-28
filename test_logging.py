"""
Test script to demonstrate the logging system.
Run this to see what the logs look like.
"""

import time
import asyncio
from app.utils.logging_utils import (
    logger,
    log_query,
    log_endpoint,
    log_error,
    log_tenant_action,
    timing_logger
)

def test_basic_logging():
    """Test basic log messages."""
    print("\n" + "="*80)
    print("TEST 1: Basic Info Logging")
    print("="*80)
    
    logger.info("Application started")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    

def test_query_logging():
    """Test query performance logging."""
    print("\n" + "="*80)
    print("TEST 2: Query Performance Logging")
    print("="*80)
    
    # Simulate a fast query (under 200ms threshold)
    log_query("SELECT * FROM clients WHERE tenant_id = 1", 45.2, tenant_id=1)
    
    # Simulate a slow query (over 200ms threshold) - should show WARNING
    log_query("SELECT * FROM clients JOIN interactions ON...", 350.7, tenant_id=1)


def test_endpoint_logging():
    """Test endpoint timing logs."""
    print("\n" + "="*80)
    print("TEST 3: Endpoint Timing")
    print("="*80)
    
    # Successful request
    log_endpoint("list_clients", 125.5, status_code=200)
    
    # Slow but successful request
    log_endpoint("export_report", 850.3, status_code=200)
    
    # Error response
    log_endpoint("create_client", 45.2, status_code=400)
    
    # Server error
    log_endpoint("bulk_update", 120.8, status_code=500)


def test_error_logging():
    """Test error logging with context."""
    print("\n" + "="*80)
    print("TEST 4: Error Logging")
    print("="*80)
    
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        log_error(e, "Failed to calculate project value")


def test_tenant_actions():
    """Test tenant action audit logging."""
    print("\n" + "="*80)
    print("TEST 5: Tenant Action Logging")
    print("="*80)
    
    log_tenant_action(
        action="created",
        entity_type="client",
        entity_id=123,
        tenant_id=1,
        user_id=5
    )
    
    log_tenant_action(
        action="deleted",
        entity_type="project",
        entity_id=456,
        tenant_id=1,
        user_id=5
    )


@timing_logger("test_operation")
async def decorated_operation():
    """Test the automatic timing decorator."""
    print("\n" + "="*80)
    print("TEST 6: Timing Decorator")
    print("="*80)

    # Simulate some work
    await asyncio.sleep(0.1)
    return "Operation complete"


def test_timing_decorator():
    """Ensure the decorator can wrap async functions without pytest-asyncio."""
    result = asyncio.run(decorated_operation())
    assert result == "Operation complete"


async def run_all_tests():
    """Run all logging tests."""
    print("\n" + "🔍 LOGGING SYSTEM DEMONSTRATION")
    print("This shows you what logs look like when things happen in your app.\n")
    
    test_basic_logging()
    test_query_logging()
    test_endpoint_logging()
    test_error_logging()
    test_tenant_actions()
    
    # Test decorator
    await decorated_operation()
    
    print("\n" + "="*80)
    print("✅ LOGGING TEST COMPLETE")
    print("="*80)
    print("\nWhen your app is running, you'll see logs like these in your terminal.")
    print("Look for [WARNING] messages to identify slow queries or performance issues.")
    print()


if __name__ == '__main__':
    import asyncio
    asyncio.run(run_all_tests())
