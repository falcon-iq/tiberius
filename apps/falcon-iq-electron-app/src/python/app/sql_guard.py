"""SQL validation to ensure only safe, read-only queries are executed."""

import re
from typing import Tuple, Optional
from app.config import MAX_QUERY_LIMIT, DANGEROUS_KEYWORDS


class SQLValidationError(Exception):
    """Raised when SQL validation fails."""
    pass


def validate_sql(sql: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that SQL is safe and read-only.
    
    Args:
        sql: SQL query to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        If valid: (True, None)
        If invalid: (False, error_message)
    """
    if not sql or not sql.strip():
        return False, "SQL query is empty"
    
    sql_upper = sql.upper().strip()
    
    # 1. Check for dangerous keywords
    for keyword in DANGEROUS_KEYWORDS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_upper):
            return False, f"Dangerous keyword detected: {keyword}"
    
    # 2. Must start with SELECT
    if not sql_upper.startswith('SELECT'):
        return False, "Query must start with SELECT (read-only)"
    
    # 3. Check for semicolons (prevent multiple statements)
    if ';' in sql.strip().rstrip(';'):
        return False, "Multiple statements not allowed (semicolons detected)"
    
    # 4. Check for LIMIT clause
    if 'LIMIT' not in sql_upper:
        return False, f"Query must include LIMIT clause (max: {MAX_QUERY_LIMIT})"
    
    # 5. Validate LIMIT value
    limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
    if limit_match:
        limit_value = int(limit_match.group(1))
        if limit_value > MAX_QUERY_LIMIT:
            return False, f"LIMIT {limit_value} exceeds maximum of {MAX_QUERY_LIMIT}"
        if limit_value <= 0:
            return False, "LIMIT must be greater than 0"
    else:
        return False, "Invalid LIMIT clause format"
    
    # 6. Check for comment injection attempts
    if '--' in sql or '/*' in sql or '*/' in sql:
        return False, "Comments not allowed in SQL queries"
    
    # 7. Check for string escape attempts
    if '\\x' in sql or '\\u' in sql:
        return False, "Escape sequences not allowed"
    
    return True, None


def enforce_sql_safety(sql: str) -> str:
    """
    Validate SQL and raise exception if invalid.
    
    Args:
        sql: SQL query to validate
    
    Returns:
        The original SQL if valid
    
    Raises:
        SQLValidationError: If validation fails
    """
    is_valid, error = validate_sql(sql)
    if not is_valid:
        raise SQLValidationError(f"SQL validation failed: {error}")
    return sql


def suggest_fix(sql: str, error: str) -> str:
    """
    Suggest how to fix a validation error.
    
    Args:
        sql: Original SQL
        error: Validation error message
    
    Returns:
        Suggestion for fixing the error
    """
    if "must start with SELECT" in error:
        return "Rewrite query to start with SELECT. Only read-only queries are allowed."
    
    if "LIMIT" in error:
        if "must include" in error:
            return f"Add LIMIT clause at end of query (e.g., LIMIT {MAX_QUERY_LIMIT})"
        elif "exceeds maximum" in error:
            return f"Reduce LIMIT to {MAX_QUERY_LIMIT} or less"
    
    if "Dangerous keyword" in error:
        keyword = error.split(":")[-1].strip()
        return f"Remove {keyword} - only read-only SELECT queries are allowed"
    
    if "Multiple statements" in error:
        return "Execute only one query at a time. Remove semicolons between statements."
    
    return "Rewrite query to follow safety guidelines: SELECT only, include LIMIT, no dangerous operations"
