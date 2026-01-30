"""SQLite tools for the PR Analytics Agent."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from app.config import SQLITE_PATH, MAX_QUERY_LIMIT
from app.sql_guard import enforce_sql_safety


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Get SQLite database connection.
    
    Args:
        db_path: Optional path to database file. Defaults to SQLITE_PATH from config.
    
    Returns:
        Database connection
    
    Raises:
        FileNotFoundError: If database file doesn't exist
    """
    path = db_path or SQLITE_PATH
    
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at {path}. "
            f"Please ensure the database file exists."
        )
    
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects
    return conn


def get_schema(db_path: Optional[Path] = None) -> str:
    """
    Get database schema as formatted text.
    
    Args:
        db_path: Optional path to database file
    
    Returns:
        Formatted schema text with CREATE TABLE statements and row counts
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema_parts = []
    schema_parts.append("=" * 80)
    schema_parts.append("DATABASE SCHEMA")
    schema_parts.append("=" * 80)
    schema_parts.append("")
    
    for table in tables:
        # Get CREATE statement
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,))
        create_sql = cursor.fetchone()[0]
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        schema_parts.append(f"Table: {table}")
        schema_parts.append(f"Rows: {row_count:,}")
        schema_parts.append("")
        schema_parts.append("Columns:")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = " (PRIMARY KEY)" if col[5] else ""
            schema_parts.append(f"  - {col_name}: {col_type}{is_pk}")
        schema_parts.append("")
        schema_parts.append("CREATE statement:")
        schema_parts.append(create_sql)
        schema_parts.append("")
        schema_parts.append("-" * 80)
        schema_parts.append("")
    
    conn.close()
    return "\n".join(schema_parts)


def run_query(
    sql: str,
    params: Optional[Tuple] = None,
    db_path: Optional[Path] = None,
    validate: bool = True
) -> List[Dict[str, Any]]:
    """
    Execute a read-only SQL query and return results.
    
    Args:
        sql: SQL query to execute
        params: Optional query parameters for parameterized queries
        db_path: Optional path to database file
        validate: Whether to validate SQL before execution (default: True)
    
    Returns:
        List of rows as dictionaries
    
    Raises:
        SQLValidationError: If SQL validation fails
        sqlite3.Error: If query execution fails
    """
    if validate:
        enforce_sql_safety(sql)
    
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        
        # Convert Row objects to dictionaries
        results = [dict(row) for row in rows]
        
        return results
    finally:
        conn.close()


def db_doctor(db_path: Optional[Path] = None) -> str:
    """
    Run database diagnostics and return status report.
    
    Args:
        db_path: Optional path to database file
    
    Returns:
        Formatted diagnostics report
    """
    report = []
    report.append("=" * 80)
    report.append("DATABASE DIAGNOSTICS")
    report.append("=" * 80)
    report.append("")
    
    path = db_path or SQLITE_PATH
    
    # Check file existence
    if not path.exists():
        report.append(f"❌ Database file NOT found: {path}")
        report.append("")
        report.append("Please ensure the database file exists at the expected location.")
        return "\n".join(report)
    
    report.append(f"✅ Database file found: {path}")
    report.append(f"   Size: {path.stat().st_size / 1024 / 1024:.2f} MB")
    report.append("")
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Get table count and row counts
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        report.append(f"✅ Connection successful")
        report.append(f"   Tables found: {len(tables)}")
        report.append("")
        
        report.append("Table Summary:")
        report.append("-" * 80)
        
        total_rows = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            total_rows += row_count
            
            # Get a sample row if table has data
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = cursor.fetchone()
            has_data = "✅" if sample else "⚠️ "
            
            report.append(f"  {has_data} {table}: {row_count:,} rows")
        
        report.append("")
        report.append(f"Total rows across all tables: {total_rows:,}")
        report.append("")
        report.append("✅ Database is healthy and ready!")
        
        conn.close()
        
    except Exception as e:
        report.append(f"❌ Error connecting to database: {e}")
    
    return "\n".join(report)


def get_sample_data(table: str, limit: int = 5, db_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Get sample data from a table.
    
    Args:
        table: Table name
        limit: Number of rows to return (max 20)
        db_path: Optional path to database file
    
    Returns:
        List of sample rows as dictionaries
    """
    limit = min(limit, 20)  # Safety limit
    sql = f"SELECT * FROM {table} LIMIT {limit}"
    return run_query(sql, db_path=db_path, validate=False)
