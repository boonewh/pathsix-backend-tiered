from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy import create_engine, event
from app.config import SQLALCHEMY_DATABASE_URI, SLOW_QUERY_THRESHOLD_MS
import os
import logging
import time

# Set up query logging
query_logger = logging.getLogger('sqlalchemy.queries')

def _log_slow_query(conn, cursor, statement, parameters, context, executemany):
    """Log slow database queries for performance monitoring."""
    duration_ms = (time.time() - context._query_start_time) * 1000
    
    if duration_ms > SLOW_QUERY_THRESHOLD_MS:
        query_logger.warning(
            f"Slow query detected ({duration_ms:.2f}ms): {statement[:200]}..."
        )

engine = create_engine(
    SQLALCHEMY_DATABASE_URI, 
    echo=False,  # Don't echo all queries, we'll log slow ones only
    future=True
)

# Attach query timing event listener
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    _log_slow_query(conn, cursor, statement, parameters, context, executemany)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()


# TODO: CLEANUP - This function is redundant with the existing pattern.
# The original repo used `Base.metadata.create_all(bind=engine)` directly (see reset_tables.py).
# This wrapper was added for convenience in setup_dev.py but can be removed in favor of
# the original approach. Consider removing this and updating setup_dev.py to use the
# standard pattern: `from app.database import Base, engine; Base.metadata.create_all(bind=engine)`
def init_db():
    """
    Initialize the database by creating all tables.
    This is safe to run multiple times - it only creates tables that don't exist.

    NOTE: This is just a convenience wrapper around Base.metadata.create_all(bind=engine)
    """
    # Import all models to ensure they're registered with Base.metadata
    import app.models

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")