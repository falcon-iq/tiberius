"""Tests for SQL validation."""

import pytest
from app.sql_guard import validate_sql, SQLValidationError, enforce_sql_safety, suggest_fix


class TestSQLValidation:
    """Test SQL validation rules."""
    
    def test_valid_select_query(self):
        """Valid SELECT query should pass."""
        sql = "SELECT * FROM users LIMIT 10"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None
    
    def test_missing_limit(self):
        """Query without LIMIT should fail."""
        sql = "SELECT * FROM users"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "LIMIT" in error
    
    def test_dangerous_insert(self):
        """INSERT query should fail."""
        sql = "INSERT INTO users VALUES (1, 'test') LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "INSERT" in error
    
    def test_dangerous_update(self):
        """UPDATE query should fail."""
        sql = "UPDATE users SET name='test' LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "UPDATE" in error
    
    def test_dangerous_delete(self):
        """DELETE query should fail."""
        sql = "DELETE FROM users WHERE id=1 LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "DELETE" in error
    
    def test_dangerous_drop(self):
        """DROP query should fail."""
        sql = "DROP TABLE users LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "DROP" in error
    
    def test_dangerous_pragma(self):
        """PRAGMA query should fail."""
        sql = "PRAGMA table_info(users) LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "PRAGMA" in error
    
    def test_multiple_statements(self):
        """Multiple statements (semicolons) should fail."""
        sql = "SELECT * FROM users LIMIT 10; SELECT * FROM goals LIMIT 10"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "Multiple statements" in error or "semicolons" in error
    
    def test_limit_too_high(self):
        """LIMIT exceeding MAX_QUERY_LIMIT should fail."""
        sql = "SELECT * FROM users LIMIT 500"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "exceeds maximum" in error
    
    def test_limit_zero(self):
        """LIMIT 0 should fail."""
        sql = "SELECT * FROM users LIMIT 0"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "greater than 0" in error
    
    def test_sql_comments(self):
        """SQL comments should fail."""
        sql = "SELECT * FROM users -- comment\nLIMIT 10"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "Comments not allowed" in error
    
    def test_complex_valid_query(self):
        """Complex but valid query should pass."""
        sql = """
        SELECT u.userName, COUNT(*) as pr_count
        FROM users u
        JOIN pr_stats ps ON u.userName = ps.username
        WHERE ps.task_type = 'authored'
        GROUP BY u.userName
        ORDER BY pr_count DESC
        LIMIT 20
        """
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        assert error is None
    
    def test_case_insensitive_keywords(self):
        """Keyword detection should be case-insensitive."""
        sql = "select * from users limit 10"
        is_valid, error = validate_sql(sql)
        assert is_valid is True
        
        sql = "InSeRt InTo users VALUES (1) LIMIT 1"
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "INSERT" in error
    
    def test_empty_query(self):
        """Empty query should fail."""
        sql = ""
        is_valid, error = validate_sql(sql)
        assert is_valid is False
        assert "empty" in error
    
    def test_enforce_safety_raises_exception(self):
        """enforce_sql_safety should raise exception on invalid SQL."""
        sql = "INSERT INTO users VALUES (1) LIMIT 1"
        with pytest.raises(SQLValidationError):
            enforce_sql_safety(sql)
    
    def test_enforce_safety_returns_sql_if_valid(self):
        """enforce_sql_safety should return SQL if valid."""
        sql = "SELECT * FROM users LIMIT 10"
        result = enforce_sql_safety(sql)
        assert result == sql


class TestSuggestFix:
    """Test SQL fix suggestions."""
    
    def test_suggest_fix_missing_select(self):
        """Suggest fix for non-SELECT query."""
        sql = "UPDATE users SET name='test'"
        error = "Query must start with SELECT (read-only)"
        suggestion = suggest_fix(sql, error)
        assert "SELECT" in suggestion
        assert "read-only" in suggestion
    
    def test_suggest_fix_missing_limit(self):
        """Suggest fix for missing LIMIT."""
        sql = "SELECT * FROM users"
        error = "Query must include LIMIT clause"
        suggestion = suggest_fix(sql, error)
        assert "LIMIT" in suggestion
    
    def test_suggest_fix_dangerous_keyword(self):
        """Suggest fix for dangerous keyword."""
        sql = "DROP TABLE users"
        error = "Dangerous keyword detected: DROP"
        suggestion = suggest_fix(sql, error)
        assert "DROP" in suggestion
        assert "read-only" in suggestion


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
