"""
============================================================================
INVENTRA - Database Utilities
============================================================================

This module provides database operations for the Inventra inventory system.

ARCHITECTURE:
------------
- Uses SQLite for simplicity (can be upgraded to PostgreSQL later)
- Single connection pattern with thread-local storage for safety
- All queries are parameterized to prevent SQL injection

KEY FUNCTIONS:
-------------
- init_db(): Initialize database with schema and seed data
- get_connection(): Get thread-safe database connection
- run_query(): Execute SELECT queries and return results as DataFrame

============================================================================
"""

import os
import sqlite3
import threading
from pathlib import Path
from typing import Optional, List, Any, Dict

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default to in-memory database if not specified
DATABASE_PATH = os.getenv("DATABASE_PATH", ":memory:")

# Thread-local storage for database connections
# This ensures each thread gets its own connection (SQLite requirement)
_thread_local = threading.local()


# =============================================================================
# CONNECTION MANAGEMENT
# =============================================================================

def get_connection() -> sqlite3.Connection:
    """
    Get a thread-safe SQLite database connection.
    
    Uses thread-local storage to ensure each thread has its own connection,
    which is required by SQLite for thread safety.
    
    Returns:
        sqlite3.Connection: Active database connection
        
    Example:
        >>> conn = get_connection()
        >>> cursor = conn.execute("SELECT * FROM inventory")
    """
    # Check if this thread already has a connection
    if not hasattr(_thread_local, "connection") or _thread_local.connection is None:
        # Create new connection for this thread
        _thread_local.connection = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False  # Allow connection to be used in callbacks
        )
        # Enable foreign keys for data integrity
        _thread_local.connection.execute("PRAGMA foreign_keys = ON")
        # Return results as Row objects (dict-like access)
        _thread_local.connection.row_factory = sqlite3.Row
    
    return _thread_local.connection


def close_connection() -> None:
    """
    Close the database connection for the current thread.
    
    Should be called during cleanup or shutdown.
    """
    if hasattr(_thread_local, "connection") and _thread_local.connection:
        _thread_local.connection.close()
        _thread_local.connection = None


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db(seed_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize the database with schema and seed data.
    
    This function:
    1. Creates the database file (or uses in-memory)
    2. Executes the seed SQL file to create tables and insert data
    3. Returns status information about the initialization
    
    Args:
        seed_file: Path to SQL seed file. If None, uses default seed.sql
        
    Returns:
        dict: Status information including table counts
        
    Example:
        >>> status = init_db()
        >>> print(status)
        {'ok': True, 'tables': ['inventory', 'suppliers'], 'row_count': 50}
    """
    conn = get_connection()
    
    # Determine seed file path
    if seed_file is None:
        # Default: seed.sql in the same directory as this file
        seed_file = Path(__file__).parent / "seed.sql"
    
    seed_path = Path(seed_file)
    
    if not seed_path.exists():
        return {
            "ok": False, 
            "error": f"Seed file not found: {seed_path}"
        }
    
    try:
        # Read and execute seed SQL
        with open(seed_path, "r", encoding="utf-8") as f:
            sql_script = f.read()
        
        conn.executescript(sql_script)
        conn.commit()
        
        # Get table information
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        table_names = [t["name"] for t in tables]
        
        # Count total rows
        total_rows = 0
        for table in table_names:
            count = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()["cnt"]
            total_rows += count
        
        return {
            "ok": True,
            "tables": table_names,
            "total_rows": total_rows,
            "database": DATABASE_PATH
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


# =============================================================================
# QUERY UTILITIES
# =============================================================================

def run_query(query: str, params: Optional[tuple] = None) -> pd.DataFrame:
    """
    Execute a SELECT query and return results as a pandas DataFrame.
    
    This is the primary function for agents to retrieve data.
    Only SELECT queries are allowed for safety.
    
    Args:
        query: SQL SELECT query string
        params: Optional tuple of parameters for parameterized queries
        
    Returns:
        pd.DataFrame: Query results as a DataFrame
        
    Raises:
        ValueError: If query is not a SELECT statement
        
    Example:
        >>> df = run_query("SELECT * FROM inventory WHERE category = ?", ("Umbrellas",))
        >>> print(df.head())
    """
    # Security: Only allow SELECT queries
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT") and not query_upper.startswith("WITH"):
        raise ValueError("Only SELECT or WITH queries are allowed for safety")
    
    conn = get_connection()
    
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
        
    except Exception as e:
        # Return empty DataFrame with error info
        return pd.DataFrame({"error": [str(e)]})


def get_table_schema(table_name: str) -> List[Dict[str, str]]:
    """
    Get the schema (column definitions) for a table.
    
    Useful for agents to understand what data is available.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        list: List of dicts with column info (name, type, nullable, etc.)
        
    Example:
        >>> schema = get_table_schema("inventory")
        >>> for col in schema:
        ...     print(f"{col['name']}: {col['type']}")
    """
    conn = get_connection()
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    return [
        {
            "name": col["name"],
            "type": col["type"],
            "nullable": not col["notnull"],
            "primary_key": bool(col["pk"]),
            "default": col["dflt_value"]
        }
        for col in columns
    ]


def get_all_tables() -> List[str]:
    """
    Get list of all tables in the database.
    
    Returns:
        list: Table names
        
    Example:
        >>> tables = get_all_tables()
        >>> print(tables)
        ['inventory', 'suppliers', 'weather_sensitive_products']
    """
    conn = get_connection()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [t["name"] for t in tables]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_inventory_summary() -> pd.DataFrame:
    """
    Get a summary of inventory grouped by category.
    
    This is a convenience function for common inventory analysis.
    
    Returns:
        pd.DataFrame: Summary with category, total units, low stock count
    """
    query = """
    SELECT 
        category,
        COUNT(*) as product_count,
        SUM(units_on_hand) as total_units,
        SUM(CASE WHEN units_on_hand <= reorder_point THEN 1 ELSE 0 END) as low_stock_count,
        AVG(unit_cost) as avg_cost
    FROM inventory
    GROUP BY category
    ORDER BY low_stock_count DESC
    """
    return run_query(query)


def get_low_stock_items() -> pd.DataFrame:
    """
    Get all items that are at or below their reorder point.
    
    Returns:
        pd.DataFrame: Low stock items with supplier info
    """
    query = """
    SELECT 
        i.sku_id,
        i.sku_name,
        i.category,
        i.units_on_hand,
        i.reorder_point,
        i.units_on_hand - i.reorder_point as stock_deficit,
        s.supplier_name,
        s.lead_time_days
    FROM inventory i
    JOIN suppliers s ON i.supplier_id = s.supplier_id
    WHERE i.units_on_hand <= i.reorder_point
    ORDER BY stock_deficit ASC
    """
    return run_query(query)
