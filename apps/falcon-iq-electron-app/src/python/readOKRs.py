#!/usr/bin/env python3
"""
Read OKRs/Goals from SQLite Database

Reads goals from the Falcon IQ SQLite database and transforms them into
a structured format.

Usage:
    python readOKRs.py [--db-path PATH] [--output PATH]
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


def read_okrs_from_db(conn: sqlite3.Connection) -> List[Dict]:
    """
    Read all OKRs/goals from the database and transform them.
    
    Args:
        conn: Database connection
    
    Returns:
        List of OKR dictionaries in the required format
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            goal,
            start_date,
            end_date
        FROM goals
        ORDER BY start_date DESC, id DESC
    """)
    
    rows = cursor.fetchall()
    okrs = []
    
    for row in rows:
        okr = {
            "id": row['id'],
            "goal": row['goal'] or '',
            "startDate": row['start_date'] or '',
            "endDate": row['end_date'] or ''
        }
        
        okrs.append(okr)
    
    return okrs


def get_okrs_from_database(db_path: Path, quiet: bool = True) -> List[Dict]:
    """
    Get OKRs from the database.
    Convenience function that handles connection and cleanup.
    
    Args:
        db_path: Path to the database file
        quiet: If True, suppress print statements (default: True for library use)
    
    Returns:
        List of OKR dictionaries in the required format
    """
    conn = connect_to_database(db_path, quiet=quiet)
    if not conn:
        return []
    
    try:
        okrs = read_okrs_from_db(conn)
        return okrs
    finally:
        conn.close()


def print_okrs(okrs: List[Dict]):
    """
    Print OKRs in a formatted way.
    
    Args:
        okrs: List of OKR dictionaries
    """
    print(f"\n{'='*80}")
    print(f"🎯 Found {len(okrs)} OKR(s)/Goal(s):")
    print(f"{'='*80}\n")
    
    if not okrs:
        print("   (No OKRs/goals found)")
        return
    
    for i, okr in enumerate(okrs, 1):
        print(f"OKR {i} (ID: {okr['id']}):")
        print(f"   goal: {okr['goal']}")
        print(f"   startDate: {okr['startDate']}")
        print(f"   endDate: {okr['endDate']}")
        print()


def save_okrs_to_json(okrs: List[Dict], output_path: Path):
    """
    Save OKRs to a JSON file.
    
    Args:
        okrs: List of OKR dictionaries
        output_path: Path to output JSON file
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(okrs, f, indent=2)
        print(f"💾 Saved {len(okrs)} OKR(s) to: {output_path}")
    except Exception as e:
        print(f"❌ Error saving to file: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Read OKRs/goals from SQLite database and transform to JSON format'
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
    
    print("🔄 Reading OKRs/Goals from Database")
    print("=" * 80)
    print()
    
    # Connect to database
    db_path = Path(args.db_path)
    conn = connect_to_database(db_path)
    if not conn:
        return
    
    # Read and transform OKRs
    okrs = read_okrs_from_db(conn)
    
    # Close connection
    conn.close()
    print("✅ Database connection closed")
    
    # Print OKRs
    print_okrs(okrs)
    
    # Optionally save to file
    if args.output:
        output_path = Path(args.output)
        save_okrs_to_json(okrs, output_path)
    
    # Print JSON output
    print(f"\n{'='*80}")
    print("📋 JSON Output:")
    print(f"{'='*80}\n")
    print(json.dumps(okrs, indent=2))


if __name__ == "__main__":
    main()
