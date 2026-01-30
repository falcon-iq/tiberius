"""Tests for SQLite tools."""

import pytest
import sqlite3
import tempfile
from pathlib import Path

from app.tools_sqlite import (
    get_db_connection,
    get_schema,
    run_query,
    db_doctor,
    get_sample_data
)
from app.sql_guard import SQLValidationError


@pytest.fixture
def temp_db():
    """Create a temporary test database."""
    # Create temp database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    # Initialize with test schema
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create test tables
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            userName TEXT NOT NULL,
            firstName TEXT,
            lastName TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE pr_stats (
            id INTEGER PRIMARY KEY,
            username TEXT,
            repo TEXT,
            pr_number INTEGER,
            total_comments INTEGER
        )
    """)
    
    # Insert test data
    cursor.execute("INSERT INTO users VALUES (1, 'testuser', 'Test', 'User')")
    cursor.execute("INSERT INTO users VALUES (2, 'alice', 'Alice', 'Smith')")
    
    cursor.execute("INSERT INTO pr_stats VALUES (1, 'testuser', 'repo1', 101, 5)")
    cursor.execute("INSERT INTO pr_stats VALUES (2, 'testuser', 'repo1', 102, 10)")
    cursor.execute("INSERT INTO pr_stats VALUES (3, 'alice', 'repo2', 201, 3)")
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    db_path.unlink()


class TestDatabaseConnection:
    """Test database connection."""
    
    def test_get_db_connection_success(self, temp_db):
        """Should connect to existing database."""
        conn = get_db_connection(temp_db)
        assert conn is not None
        
        # Verify connection works
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        assert count == 2
        
        conn.close()
    
    def test_get_db_connection_missing_file(self):
        """Should raise error for missing database."""
        with pytest.raises(FileNotFoundError):
            get_db_connection(Path("/nonexistent/database.db"))


class TestGetSchema:
    """Test schema retrieval."""
    
    def test_get_schema_returns_text(self, temp_db):
        """Should return schema as formatted text."""
        schema = get_schema(temp_db)
        
        assert isinstance(schema, str)
        assert "users" in schema
        assert "pr_stats" in schema
        assert "userName" in schema
        assert "total_comments" in schema
    
    def test_get_schema_includes_row_counts(self, temp_db):
        """Should include row counts."""
        schema = get_schema(temp_db)
        
        assert "Rows: 2" in schema  # users table
        assert "Rows: 3" in schema  # pr_stats table


class TestRunQuery:
    """Test query execution."""
    
    def test_run_query_success(self, temp_db):
        """Should execute valid query."""
        sql = "SELECT * FROM users LIMIT 10"
        results = run_query(sql, db_path=temp_db)
        
        assert len(results) == 2
        assert results[0]['userName'] == 'testuser'
        assert results[1]['userName'] == 'alice'
    
    def test_run_query_with_filter(self, temp_db):
        """Should execute query with WHERE clause."""
        sql = "SELECT * FROM users WHERE userName = 'testuser' LIMIT 10"
        results = run_query(sql, db_path=temp_db)
        
        assert len(results) == 1
        assert results[0]['userName'] == 'testuser'
    
    def test_run_query_aggregation(self, temp_db):
        """Should execute aggregation query."""
        sql = "SELECT username, SUM(total_comments) as total FROM pr_stats GROUP BY username LIMIT 10"
        results = run_query(sql, db_path=temp_db)
        
        assert len(results) == 2
        # Find testuser's row
        testuser_row = next(r for r in results if r['username'] == 'testuser')
        assert testuser_row['total'] == 15  # 5 + 10
    
    def test_run_query_validation_failure(self, temp_db):
        """Should raise error for invalid SQL."""
        sql = "INSERT INTO users VALUES (3, 'bad') LIMIT 1"
        
        with pytest.raises(SQLValidationError):
            run_query(sql, db_path=temp_db)
    
    def test_run_query_skip_validation(self, temp_db):
        """Should allow skipping validation."""
        # This would normally fail validation (no LIMIT)
        sql = "SELECT * FROM users"
        
        # Should raise error without validate=False
        with pytest.raises(SQLValidationError):
            run_query(sql, db_path=temp_db, validate=True)
        
        # Should work with validate=False
        results = run_query(sql, db_path=temp_db, validate=False)
        assert len(results) == 2


class TestDBDoctor:
    """Test database diagnostics."""
    
    def test_db_doctor_healthy_database(self, temp_db):
        """Should report healthy database."""
        report = db_doctor(temp_db)
        
        assert "✅" in report
        assert "Database file found" in report
        assert "Connection successful" in report
        assert "users" in report
        assert "pr_stats" in report
    
    def test_db_doctor_missing_database(self):
        """Should report missing database."""
        report = db_doctor(Path("/nonexistent/database.db"))
        
        assert "❌" in report
        assert "NOT found" in report


class TestGetSampleData:
    """Test sample data retrieval."""
    
    def test_get_sample_data(self, temp_db):
        """Should return sample rows."""
        samples = get_sample_data("users", limit=1, db_path=temp_db)
        
        assert len(samples) == 1
        assert 'userName' in samples[0]
    
    def test_get_sample_data_respects_limit(self, temp_db):
        """Should respect limit parameter."""
        samples = get_sample_data("pr_stats", limit=2, db_path=temp_db)
        
        assert len(samples) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
