#!/usr/bin/env python3
"""
Read OKRs/Goals from SQLite Database

Reads goals from the Falcon IQ SQLite database and transforms them into
a structured format. Supports searching OKRs by name.

Usage:
    python readOKRs.py [--output PATH] [--search TERM] [--base-dir PATH]
    
Examples:
    # List all OKRs
    python readOKRs.py
    
    # Search for OKRs containing "resiliency"
    python readOKRs.py --search resiliency
    
    # Search and save to JSON
    python readOKRs.py --search "Q1 2024" --output okrs.json
    
    # Use custom base directory
    python readOKRs.py --base-dir ~/Library/Application\ Support/Falcon\ IQ --search resiliency
"""

import sqlite3
import json
import argparse
import os
from pathlib import Path
from typing import List, Dict, Optional
from common import get_base_dir, getDBPath, set_base_dir


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


def findByOkrName(conn: sqlite3.Connection, search_term: str) -> List[int]:
    """
    Find OKR IDs by searching for a term in the goal name using LIKE query.
    
    Args:
        conn: Database connection
        search_term: Search term to match against goal names (case-insensitive)
    
    Returns:
        List of OKR IDs that match the search term
        
    Example:
        >>> conn = connect_to_database(db_path)
        >>> okr_ids = findByOkrName(conn, "resiliency")
        >>> print(f"Found {len(okr_ids)} OKRs: {okr_ids}")
    """
    cursor = conn.cursor()
    
    # Use LIKE with wildcards for partial matching (case-insensitive)
    query = """
        SELECT id
        FROM goals
        WHERE goal LIKE ?
        ORDER BY start_date DESC, id DESC
    """
    
    # Add wildcards to search term
    search_pattern = f"%{search_term}%"
    
    cursor.execute(query, (search_pattern,))
    rows = cursor.fetchall()
    
    # Extract IDs from results
    okr_ids = [row['id'] for row in rows]
    
    return okr_ids


def findByOkrNameWithDetails(conn: sqlite3.Connection, search_term: str) -> List[Dict]:
    """
    Find OKRs by searching for a term in the goal name, returning full details.
    
    Args:
        conn: Database connection
        search_term: Search term to match against goal names (case-insensitive)
    
    Returns:
        List of OKR dictionaries with full details (id, goal, startDate, endDate)
        
    Example:
        >>> conn = connect_to_database(db_path)
        >>> okrs = findByOkrNameWithDetails(conn, "resiliency")
        >>> for okr in okrs:
        >>>     print(f"OKR {okr['id']}: {okr['goal']}")
    """
    cursor = conn.cursor()
    
    # Use LIKE with wildcards for partial matching (case-insensitive)
    query = """
        SELECT 
            id,
            goal,
            start_date,
            end_date
        FROM goals
        WHERE goal LIKE ?
        ORDER BY start_date DESC, id DESC
    """
    
    # Add wildcards to search term
    search_pattern = f"%{search_term}%"
    
    cursor.execute(query, (search_pattern,))
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
        '--output',
        type=str,
        help='Optional: Path to save the output JSON file'
    )
    parser.add_argument(
        '--search',
        type=str,
        help='Search for OKRs by name (case-insensitive, partial match)'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        help='Base directory path (overrides FALCON_BASE_DIR env var and config)'
    )
    
    args = parser.parse_args()
    
    # Set base directory BEFORE getting database path
    if args.base_dir:
        base_dir_path = Path(args.base_dir).expanduser()
        set_base_dir(str(base_dir_path))
        print(f"📁 Using base directory: {base_dir_path}")
        print()
    
    print("🔄 Reading OKRs/Goals from Database")
    print("=" * 80)
    print()
    
    # Connect to database
    base_dir = get_base_dir()
    db_path = getDBPath(base_dir)
    conn = connect_to_database(db_path)
    if not conn:
        return
    
    # If search term provided, use findByOkrName
    if args.search:
        print(f"🔍 Searching for OKRs matching: '{args.search}'")
        print("=" * 80)
        print()
        
        # Get OKR IDs only
        okr_ids = findByOkrName(conn, args.search)
        print(f"📋 Found {len(okr_ids)} matching OKR ID(s):")
        print(f"   {okr_ids}")
        print()
        
        # Get full OKR details
        okrs = findByOkrNameWithDetails(conn, args.search)
        
        # Close connection
        conn.close()
        print("✅ Database connection closed")
        
        # Print OKRs
        print_okrs(okrs)
    else:
        # Read and transform all OKRs
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
