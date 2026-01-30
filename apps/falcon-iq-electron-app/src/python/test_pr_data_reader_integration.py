#!/usr/bin/env python3
"""
Test script to verify prDataReader works correctly when FALCON_BASE_DIR is set.
This simulates how server.py would use prDataReader.
"""

import os
import sys

# SIMULATE SERVER.PY: Set environment variable BEFORE any imports
# This is what server.py does at the very top
if len(sys.argv) > 1:
    BASE_DIR = sys.argv[1]
else:
    BASE_DIR = os.path.expanduser("~/Library/Application Support/Falcon IQ")

print(f"Setting FALCON_BASE_DIR to: {BASE_DIR}")
os.environ['FALCON_BASE_DIR'] = BASE_DIR
os.environ['FALCON_IS_DEV'] = '1'

# NOW import modules (after environment is set)
import sqlite3
from prDataReader import get_pr_details
from common import getDBPath, get_base_dir

def test_integration():
    """Test that prDataReader works with environment variable set."""
    print("=" * 80)
    print("Testing prDataReader Integration (simulating server.py)")
    print("=" * 80)
    print()
    
    # Verify environment variable is set
    print(f"✅ FALCON_BASE_DIR environment variable: {os.environ.get('FALCON_BASE_DIR')}")
    
    # Get base directory (should use environment variable)
    base_dir = get_base_dir()
    print(f"✅ Base directory from common.py: {base_dir}")
    print()
    
    # Connect to database
    db_path = getDBPath(base_dir)
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"✅ Database found: {db_path}")
    db_conn = sqlite3.connect(str(db_path))
    print()
    
    # Find a sample PR
    cursor = db_conn.cursor()
    cursor.execute("SELECT pr_id, username FROM pr_stats WHERE repo IS NOT NULL LIMIT 1")
    row = cursor.fetchone()
    
    if not row:
        print("❌ No PRs found in database")
        db_conn.close()
        return False
    
    test_pr_id = row[0]
    test_username = row[1]
    
    print(f"Testing with PR #{test_pr_id} (user: {test_username})")
    print()
    
    # Call get_pr_details WITHOUT passing base_dir
    # It should use the environment variable automatically
    print("Calling get_pr_details (no base_dir parameter)...")
    pr_details = get_pr_details(db_conn, pr_id=test_pr_id, username=test_username)
    
    if pr_details:
        print("✅ SUCCESS! PR details retrieved:")
        print(f"   Title: {pr_details['pr_title']}")
        print(f"   Author: {pr_details['pr_author']}")
        print(f"   Repo: {pr_details['owner']}/{pr_details['repo']}")
        print(f"   URL: {pr_details['pr_html_url']}")
        print()
        print("✅ Integration test PASSED!")
        print("   prDataReader correctly uses FALCON_BASE_DIR from environment")
        return True
    else:
        print("❌ Failed to retrieve PR details")
        return False
    
    db_conn.close()


if __name__ == "__main__":
    print()
    success = test_integration()
    print()
    print("=" * 80)
    if success:
        print("✅ TEST PASSED - Ready for server.py integration")
    else:
        print("❌ TEST FAILED - Check configuration")
    print("=" * 80)
    print()
    
    sys.exit(0 if success else 1)
