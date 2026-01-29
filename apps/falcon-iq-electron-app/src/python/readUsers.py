#!/usr/bin/env python3
"""
Read Users from SQLite Database

Reads users from the Falcon IQ SQLite database and transforms them into
the users.json format.

Usage:
    python readUsers.py [--db-path PATH] [--output PATH]
"""

import sqlite3
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional


def connect_to_database(db_path: Path, quiet: bool = False) -> Optional[sqlite3.Connection]:
    """
    Connect to the SQLite database.
    
    Args:
        db_path: Path to the database file
        quiet: If True, suppress print statements (default: False)
    
    Returns:
        Database connection or None if failed
    """
    if not db_path.exists():
        if not quiet:
            print(f"❌ Database not found at: {db_path}")
        return None
    
    if not quiet:
        print(f"📁 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    except Exception as e:
        if not quiet:
            print(f"❌ Error connecting to database: {e}")
        return None


def read_users_from_db(conn: sqlite3.Connection) -> List[Dict]:
    """
    Read all users from the database and transform them.
    
    Args:
        conn: Database connection
    
    Returns:
        List of user dictionaries in the required format
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            username,
            github_suffix,
            email_address,
            firstname,
            lastname
        FROM users
        ORDER BY username
    """)
    
    rows = cursor.fetchall()
    users = []
    
    for row in rows:
        username = row['username']
        github_suffix = row['github_suffix'] or ''
        
        # Calculate prUserName: userName + "_" + github_suffix
        pr_user_name = f"{username}_{github_suffix}" if github_suffix else username
        
        user = {
            "firstName": row['firstname'] or '',
            "lastName": row['lastname'] or '',
            "userName": username,
            "prUserName": pr_user_name
        }
        
        users.append(user)
    
    return users


def get_users_from_database(db_path: Path, quiet: bool = True) -> List[Dict]:
    """
    Get users from the database.
    Convenience function that handles connection and cleanup.
    
    Args:
        db_path: Path to the database file
        quiet: If True, suppress print statements (default: True for library use)
    
    Returns:
        List of user dictionaries in the required format
    """
    conn = connect_to_database(db_path, quiet=quiet)
    if not conn:
        return []
    
    try:
        users = read_users_from_db(conn)
        return users
    finally:
        conn.close()


def print_users(users: List[Dict]):
    """
    Print users in a formatted way.
    
    Args:
        users: List of user dictionaries
    """
    print(f"\n{'='*80}")
    print(f"👥 Found {len(users)} user(s):")
    print(f"{'='*80}\n")
    
    if not users:
        print("   (No users found)")
        return
    
    for i, user in enumerate(users, 1):
        print(f"User {i}:")
        print(f"   firstName: {user['firstName']}")
        print(f"   lastName: {user['lastName']}")
        print(f"   userName: {user['userName']}")
        print(f"   prUserName: {user['prUserName']}")
        print()


def save_users_to_json(users: List[Dict], output_path: Path):
    """
    Save users to a JSON file.
    
    Args:
        users: List of user dictionaries
        output_path: Path to output JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(users, f, indent=2)
        print(f"💾 Saved {len(users)} user(s) to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving to file: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Read users from SQLite database and transform to users.json format'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default=str(Path.home() / "Library" / "Application Support" / "Falcon IQ" / "database.dev.db"),
        help='Path to the SQLite database file (default: ~/Library/Application Support/Falcon IQ/database.dev.db)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Optional: Path to save the output JSON file'
    )
    
    args = parser.parse_args()
    
    print("🔄 Reading Users from Database")
    print("=" * 80)
    print()
    
    # Connect to database
    db_path = Path(args.db_path)
    conn = connect_to_database(db_path)
    if not conn:
        return
    
    # Read and transform users
    users = read_users_from_db(conn)
    
    # Close connection
    conn.close()
    print("✅ Database connection closed")
    
    # Print users
    print_users(users)
    
    # Optionally save to file
    if args.output:
        output_path = Path(args.output)
        save_users_to_json(users, output_path)
    
    # Print JSON output
    print(f"\n{'='*80}")
    print("📋 JSON Output:")
    print(f"{'='*80}\n")
    print(json.dumps(users, indent=2))


if __name__ == "__main__":
    main()
