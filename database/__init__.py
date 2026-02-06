# ============================================================================
# INVENTRA - Database Package
# ============================================================================
# 
# This package handles all database operations for the Inventra system.
# 
# Components:
# - db.py: Database connection, initialization, and query utilities
# - seed.sql: Initial data for inventory, suppliers, and products
#
# Usage:
#   from database import init_db, get_connection, run_query
# ============================================================================

from .db import init_db, get_connection, run_query

__all__ = ["init_db", "get_connection", "run_query"]
