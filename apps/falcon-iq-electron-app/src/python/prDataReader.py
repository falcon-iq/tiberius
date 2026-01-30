#!/usr/bin/env python3
"""
PR Data Reader

Reads PR details and comments from the filesystem based on data stored in SQLite.
Provides utilities to fetch PR metadata, comments, and reviews from CSV files.

Usage as module (from server.py or other scripts):
    
    # Option 1: When FALCON_BASE_DIR environment variable is set (e.g., by server.py)
    from prDataReader import get_pr_details, get_comment_details, get_pr_files
    import sqlite3
    from common import getDBPath, get_base_dir
    
    base_dir = get_base_dir()  # Uses FALCON_BASE_DIR env var
    db_conn = sqlite3.connect(str(getDBPath(base_dir)))
    
    # Get PR details
    pr_details = get_pr_details(db_conn, pr_id=12345, username="npurwar")
    
    # Get comment details
    comment = get_comment_details(db_conn, pr_id=12345, comment_id=98765)
    
    # Get all files changed in PR
    files = get_pr_files(db_conn, pr_id=12345)
    
    # Option 2: Override base_dir programmatically
    from prDataReader import get_pr_details, get_comment_details, get_pr_files, initialize_base_dir
    
    initialize_base_dir("/custom/path/to/base/dir")
    pr_details = get_pr_details(db_conn, pr_id=12345)
    comment = get_comment_details(db_conn, pr_id=12345, comment_id=98765)
    files = get_pr_files(db_conn, pr_id=12345)
    
Usage as CLI:
    python prDataReader.py 9258 --base-dir ~/path/to/base
    python prDataReader.py 9258 --username npurwar
    python prDataReader.py  # List sample PRs
    
Integration with server.py:
    The server.py sets FALCON_BASE_DIR environment variable at the top before
    any imports. This means prDataReader.py will automatically use the correct
    base directory when imported and called from server.py endpoints.
    No additional setup needed!
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd
from common import load_all_config, getDBPath, set_base_dir


def initialize_base_dir(base_dir: str):
    """
    Initialize the base directory for PR data reader.
    
    This should be called before using any other functions in this module
    if you need to override the base directory from config or environment.
    
    Args:
        base_dir: Path to the base directory
    
    Note:
        If FALCON_BASE_DIR environment variable is already set (e.g., by server.py),
        this function is optional as common.py will use that automatically.
    """
    set_base_dir(base_dir)


def get_pr_details(
    db_conn: sqlite3.Connection,
    pr_id: int,
    username: Optional[str] = None,
    base_dir: Optional[Path] = None
) -> Optional[Dict]:
    """
    Get PR details from filesystem based on pr_stats table entry.
    
    Args:
        db_conn: SQLite database connection
        pr_id: PR number/ID
        username: Optional username to filter (if multiple users have same PR)
        base_dir: Optional base directory override (only needed if FALCON_BASE_DIR env var not set)
    
    Returns:
        Dictionary with PR details or None if not found
        
    Example (when called from server.py - base_dir from environment):
        >>> pr_details = get_pr_details(db_conn, pr_id=12345, username="npurwar")
        
    Example (when called with explicit override):
        >>> pr_details = get_pr_details(db_conn, pr_id=12345, base_dir=Path("/custom/path"))
    """
    # Set global base_dir if explicitly provided (overrides environment variable)
    # Note: If called from server.py, FALCON_BASE_DIR env var is already set
    if base_dir is not None:
        set_base_dir(str(base_dir))
    
    # Query pr_stats table to get repo information
    cursor = db_conn.cursor()
    
    if username:
        query = """
            SELECT username, pr_id, repo, reviewed_authored, author_of_pr
            FROM pr_stats
            WHERE pr_id = ? AND username = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id, username))
    else:
        query = """
            SELECT username, pr_id, repo, reviewed_authored, author_of_pr
            FROM pr_stats
            WHERE pr_id = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id,))
    
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ PR {pr_id} not found in pr_stats table")
        return None
    
    # Parse row data
    username_from_db = row[0]
    pr_number = row[1]
    repo_full = row[2]
    reviewed_authored = row[3]
    author_of_pr = row[4]
    
    if not repo_full:
        print(f"❌ PR {pr_id} has no repo information in pr_stats table")
        return None
    
    # Parse repo format: {owner}/{repository}
    repo_parts = repo_full.split('/')
    if len(repo_parts) != 2:
        print(f"❌ Invalid repo format: {repo_full} (expected: owner/repository)")
        return None
    
    owner = repo_parts[0]
    repository = repo_parts[1]
    
    # Get base directory and pr_data_folder from config
    try:
        all_config = load_all_config()
        if base_dir is None:
            base_dir = all_config['paths']['base_dir']
        pr_data_folder = all_config['paths']['pr_data_folder']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None
    
    # Construct path to PR meta CSV
    # Format: {pr_data_folder}/{owner}/{repository}/pr_{id}/pr_{id}_meta.csv
    pr_meta_path = pr_data_folder / owner / repository / f"pr_{pr_number}" / f"pr_{pr_number}_meta.csv"
    
    if not pr_meta_path.exists():
        print(f"❌ PR meta file not found: {pr_meta_path}")
        return None
    
    # Load PR metadata from CSV
    try:
        df = pd.read_csv(pr_meta_path)
        
        if len(df) == 0:
            print(f"❌ PR meta file is empty: {pr_meta_path}")
            return None
        
        # Get first row (should only be one row)
        pr_row = df.iloc[0]
        
        # Convert to dictionary
        pr_details = {
            'owner': pr_row.get('owner'),
            'repo': pr_row.get('repo'),
            'pr_number': int(pr_row.get('pr_number', pr_number)),
            'pr_title': pr_row.get('pr_title'),
            'pr_body': pr_row.get('pr_body'),
            'pr_state': pr_row.get('pr_state'),
            'pr_draft': bool(pr_row.get('pr_draft', False)),
            'pr_author': pr_row.get('pr_author'),
            'pr_created_at': pr_row.get('pr_created_at'),
            'pr_updated_at': pr_row.get('pr_updated_at'),
            'pr_merged_at': pr_row.get('pr_merged_at'),
            'pr_mergeable_state': pr_row.get('pr_mergeable_state'),
            'pr_additions': int(pr_row.get('pr_additions', 0)) if pd.notna(pr_row.get('pr_additions')) else 0,
            'pr_deletions': int(pr_row.get('pr_deletions', 0)) if pd.notna(pr_row.get('pr_deletions')) else 0,
            'pr_changed_files': int(pr_row.get('pr_changed_files', 0)) if pd.notna(pr_row.get('pr_changed_files')) else 0,
            'pr_commits_count': int(pr_row.get('pr_commits_count', 0)) if pd.notna(pr_row.get('pr_commits_count')) else 0,
            'pr_issue_comments_count': int(pr_row.get('pr_issue_comments_count', 0)) if pd.notna(pr_row.get('pr_issue_comments_count')) else 0,
            'pr_review_comments_count': int(pr_row.get('pr_review_comments_count', 0)) if pd.notna(pr_row.get('pr_review_comments_count')) else 0,
            'pr_html_url': pr_row.get('pr_html_url'),
            # Add metadata from pr_stats query
            'username_from_db': username_from_db,
            'reviewed_authored': reviewed_authored,
            'author_of_pr_from_db': author_of_pr,
            'repo_full': repo_full,
            'pr_meta_path': str(pr_meta_path)
        }
        
        return pr_details
        
    except Exception as e:
        print(f"❌ Error reading PR meta file {pr_meta_path}: {e}")
        return None


def get_comment_details(
    db_conn: sqlite3.Connection,
    pr_id: int,
    comment_id: int,
    username: Optional[str] = None,
    base_dir: Optional[Path] = None
) -> Optional[Dict]:
    """
    Get comment details from filesystem based on pr_stats table entry.
    
    Args:
        db_conn: SQLite database connection
        pr_id: PR number/ID
        comment_id: Comment ID to lookup
        username: Optional username to filter (if multiple users have same PR)
        base_dir: Optional base directory override (only needed if FALCON_BASE_DIR env var not set)
    
    Returns:
        Dictionary with comment details or None if not found
        
    Example:
        >>> comment = get_comment_details(db_conn, pr_id=12345, comment_id=98765)
        >>> print(comment['body'])
        >>> print(comment['user'])
    """
    # Set global base_dir if explicitly provided
    if base_dir is not None:
        set_base_dir(str(base_dir))
    
    # Query pr_stats table to get repo information
    cursor = db_conn.cursor()
    
    if username:
        query = """
            SELECT username, pr_id, repo
            FROM pr_stats
            WHERE pr_id = ? AND username = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id, username))
    else:
        query = """
            SELECT username, pr_id, repo
            FROM pr_stats
            WHERE pr_id = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id,))
    
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ PR {pr_id} not found in pr_stats table")
        return None
    
    # Parse row data
    username_from_db = row[0]
    pr_number = row[1]
    repo_full = row[2]
    
    if not repo_full:
        print(f"❌ PR {pr_id} has no repo information in pr_stats table")
        return None
    
    # Parse repo format: {owner}/{repository}
    repo_parts = repo_full.split('/')
    if len(repo_parts) != 2:
        print(f"❌ Invalid repo format: {repo_full} (expected: owner/repository)")
        return None
    
    owner = repo_parts[0]
    repository = repo_parts[1]
    
    # Get base directory and pr_data_folder from config
    try:
        all_config = load_all_config()
        if base_dir is None:
            base_dir = all_config['paths']['base_dir']
        pr_data_folder = all_config['paths']['pr_data_folder']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None
    
    # Construct path to PR comments CSV
    # Format: {pr_data_folder}/{owner}/{repository}/pr_{id}/pr_{id}_comments.csv
    comments_csv_path = pr_data_folder / owner / repository / f"pr_{pr_number}" / f"pr_{pr_number}_comments.csv"
    
    if not comments_csv_path.exists():
        print(f"❌ Comments file not found: {comments_csv_path}")
        return None
    
    # Load comments from CSV
    try:
        df = pd.read_csv(comments_csv_path)
        
        if len(df) == 0:
            print(f"❌ Comments file is empty: {comments_csv_path}")
            return None
        
        # Find the row matching the comment_id
        matching_rows = df[df['comment_id'] == comment_id]
        
        if len(matching_rows) == 0:
            print(f"❌ Comment {comment_id} not found in {comments_csv_path}")
            return None
        
        # Get the first matching row
        comment_row = matching_rows.iloc[0]
        
        # Convert to dictionary
        comment_details = {
            'owner': comment_row.get('owner'),
            'repo': comment_row.get('repo'),
            'pr_number': int(comment_row.get('pr_number', pr_number)),
            'comment_type': comment_row.get('comment_type'),
            'comment_id': int(comment_row.get('comment_id', comment_id)),
            'user': comment_row.get('user'),
            'created_at': comment_row.get('created_at'),
            'body': comment_row.get('body'),
            'state': comment_row.get('state'),
            'is_reviewer': bool(comment_row.get('is_reviewer', False)),
            'path': comment_row.get('path'),
            'line': int(comment_row.get('line')) if pd.notna(comment_row.get('line')) else None,
            'side': comment_row.get('side'),
            # Add metadata from pr_stats query
            'username_from_db': username_from_db,
            'repo_full': repo_full,
            'comments_csv_path': str(comments_csv_path)
        }
        
        return comment_details
        
    except Exception as e:
        print(f"❌ Error reading comments file {comments_csv_path}: {e}")
        return None


def get_pr_files(
    db_conn: sqlite3.Connection,
    pr_id: int,
    username: Optional[str] = None,
    base_dir: Optional[Path] = None
) -> Optional[List[Dict]]:
    """
    Get all file changes from filesystem based on pr_stats table entry.
    
    Args:
        db_conn: SQLite database connection
        pr_id: PR number/ID
        username: Optional username to filter (if multiple users have same PR)
        base_dir: Optional base directory override (only needed if FALCON_BASE_DIR env var not set)
    
    Returns:
        List of dictionaries with file details or None if not found
        
    Example:
        >>> files = get_pr_files(db_conn, pr_id=16347)
        >>> for file in files:
        >>>     print(f"{file['filename']}: +{file['additions']} -{file['deletions']}")
    """
    # Set global base_dir if explicitly provided
    if base_dir is not None:
        set_base_dir(str(base_dir))
    
    # Query pr_stats table to get repo information
    cursor = db_conn.cursor()
    
    if username:
        query = """
            SELECT username, pr_id, repo
            FROM pr_stats
            WHERE pr_id = ? AND username = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id, username))
    else:
        query = """
            SELECT username, pr_id, repo
            FROM pr_stats
            WHERE pr_id = ?
            LIMIT 1
        """
        cursor.execute(query, (pr_id,))
    
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ PR {pr_id} not found in pr_stats table")
        return None
    
    # Parse row data
    username_from_db = row[0]
    pr_number = row[1]
    repo_full = row[2]
    
    if not repo_full:
        print(f"❌ PR {pr_id} has no repo information in pr_stats table")
        return None
    
    # Parse repo format: {owner}/{repository}
    repo_parts = repo_full.split('/')
    if len(repo_parts) != 2:
        print(f"❌ Invalid repo format: {repo_full} (expected: owner/repository)")
        return None
    
    owner = repo_parts[0]
    repository = repo_parts[1]
    
    # Get base directory and pr_data_folder from config
    try:
        all_config = load_all_config()
        if base_dir is None:
            base_dir = all_config['paths']['base_dir']
        pr_data_folder = all_config['paths']['pr_data_folder']
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None
    
    # Construct path to PR files CSV
    # Format: {pr_data_folder}/{owner}/{repository}/pr_{id}/pr_{id}_files.csv
    files_csv_path = pr_data_folder / owner / repository / f"pr_{pr_number}" / f"pr_{pr_number}_files.csv"
    
    if not files_csv_path.exists():
        print(f"❌ Files CSV not found: {files_csv_path}")
        return None
    
    # Load files from CSV
    try:
        df = pd.read_csv(files_csv_path)
        
        if len(df) == 0:
            print(f"❌ Files CSV is empty: {files_csv_path}")
            return None
        
        # Convert all rows to list of dictionaries
        files_list = []
        for idx, file_row in df.iterrows():
            file_details = {
                'owner': file_row.get('owner'),
                'repo': file_row.get('repo'),
                'pr_number': int(file_row.get('pr_number', pr_number)),
                'filename': file_row.get('filename'),
                'status': file_row.get('status'),
                'additions': int(file_row.get('additions', 0)) if pd.notna(file_row.get('additions')) else 0,
                'deletions': int(file_row.get('deletions', 0)) if pd.notna(file_row.get('deletions')) else 0,
                'changes': int(file_row.get('changes', 0)) if pd.notna(file_row.get('changes')) else 0,
                'blob_url': file_row.get('blob_url'),
                'raw_url': file_row.get('raw_url'),
                'patch': file_row.get('patch'),
            }
            files_list.append(file_details)
        
        # Add metadata
        for file_details in files_list:
            file_details['username_from_db'] = username_from_db
            file_details['repo_full'] = repo_full
            file_details['files_csv_path'] = str(files_csv_path)
        
        return files_list
        
    except Exception as e:
        print(f"❌ Error reading files CSV {files_csv_path}: {e}")
        return None


def main():
    """Test/demo the PR data reader."""
    import sys
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="PR Data Reader - Read PR details from filesystem",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python prDataReader.py 9258                           # Read PR 9258
  python prDataReader.py 9258 --username npurwar        # Read PR 9258 for specific user
  python prDataReader.py 9258 --base-dir ~/path         # Override base directory
  python prDataReader.py                                # Show sample PRs
        """
    )
    
    parser.add_argument(
        'pr_id',
        nargs='?',
        type=int,
        help='PR number/ID to lookup'
    )
    
    parser.add_argument(
        '--username',
        type=str,
        help='Username to filter (if multiple users have same PR)'
    )
    
    parser.add_argument(
        '--base-dir',
        type=str,
        help='Base directory path (overrides config file)'
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("PR Data Reader - Test Mode")
    print("=" * 80)
    print()
    
    # Set global base_dir if provided (before any config loading)
    if args.base_dir:
        base_dir = Path(args.base_dir).expanduser()
        set_base_dir(str(base_dir))
        print(f"📁 Base directory (from argument): {base_dir}")
    else:
        try:
            all_config = load_all_config()
            base_dir = all_config['paths']['base_dir']
            print(f"📁 Base directory (from config): {base_dir}")
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return
    
    # Connect to database
    try:
        db_path = getDBPath(base_dir)
        if not db_path.exists():
            print(f"❌ Database not found: {db_path}")
            return
        
        db_conn = sqlite3.connect(str(db_path))
        print(f"✅ Connected to database: {db_path}")
        print()
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return
    
    # Check if PR ID provided as command line argument
    if args.pr_id:
        test_pr_id = args.pr_id
        test_username = args.username
        print(f"Testing get_pr_details for PR #{test_pr_id}" + 
              (f" (user: {test_username})" if test_username else "") + "...")
        print()
    else:
        # Get a sample PR from the database
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT pr_id, username, repo
            FROM pr_stats
            WHERE repo IS NOT NULL
            LIMIT 5
        """)
        
        sample_prs = cursor.fetchall()
        
        if not sample_prs:
            print("❌ No PRs found in pr_stats table")
            db_conn.close()
            return
        
        print(f"Found {len(sample_prs)} sample PRs in database:")
        for pr in sample_prs:
            print(f"  - PR #{pr[0]} (user: {pr[1]}, repo: {pr[2]})")
        print()
        
        # Test get_pr_details with first PR
        test_pr_id = sample_prs[0][0]
        test_username = sample_prs[0][1]
        
        print(f"Testing get_pr_details for PR #{test_pr_id} (user: {test_username})...")
        print()
    
    pr_details = get_pr_details(db_conn, pr_id=test_pr_id, username=test_username, base_dir=base_dir)
    
    if pr_details:
        print("✅ PR Details Retrieved:")
        print("=" * 80)
        
        # Basic Info
        print(f"\n📝 BASIC INFO:")
        print(f"  PR Number: {pr_details['pr_number']}")
        print(f"  Title: {pr_details['pr_title']}")
        print(f"  State: {pr_details['pr_state']}")
        print(f"  Draft: {pr_details['pr_draft']}")
        
        # Repository
        print(f"\n📦 REPOSITORY:")
        print(f"  Owner: {pr_details['owner']}")
        print(f"  Repo: {pr_details['repo']}")
        print(f"  Full: {pr_details['repo_full']}")
        print(f"  URL: {pr_details['pr_html_url']}")
        
        # Authors
        print(f"\n👤 AUTHORS:")
        print(f"  PR Author: {pr_details['pr_author']}")
        print(f"  Author (from DB): {pr_details['author_of_pr_from_db']}")
        print(f"  Username (from DB): {pr_details['username_from_db']}")
        print(f"  Reviewed/Authored: {pr_details['reviewed_authored']}")
        
        # Dates
        print(f"\n📅 DATES:")
        print(f"  Created: {pr_details['pr_created_at']}")
        print(f"  Updated: {pr_details['pr_updated_at']}")
        print(f"  Merged: {pr_details['pr_merged_at']}")
        print(f"  Mergeable State: {pr_details['pr_mergeable_state']}")
        
        # Statistics
        print(f"\n📊 STATISTICS:")
        print(f"  Additions: +{pr_details['pr_additions']}")
        print(f"  Deletions: -{pr_details['pr_deletions']}")
        print(f"  Changed Files: {pr_details['pr_changed_files']}")
        print(f"  Commits: {pr_details['pr_commits_count']}")
        
        # Comments
        print(f"\n💬 COMMENTS:")
        print(f"  Issue Comments: {pr_details['pr_issue_comments_count']}")
        print(f"  Review Comments: {pr_details['pr_review_comments_count']}")
        
        # File Path
        print(f"\n📁 FILE:")
        print(f"  Meta Path: {pr_details['pr_meta_path']}")
        
        # Raw Body (truncated)
        print(f"\n📄 PR BODY:")
        body = pr_details.get('pr_body', '')
        if body and len(str(body)) > 200:
            print(f"  {str(body)[:200]}...")
        else:
            print(f"  {body}")
        
        print("\n" + "=" * 80)
        
        # Print all keys and values for debugging
        print("\n🔍 ALL FIELDS (for debugging):")
        print("-" * 80)
        for key, value in sorted(pr_details.items()):
            if key not in ['pr_body', 'pr_meta_path']:  # Skip long fields
                print(f"  {key}: {value}")
        print("-" * 80)
    else:
        print("❌ Failed to retrieve PR details")
    
    # Test get_comment_details if PR was found
    if pr_details:
        print()
        print("=" * 80)
        print("Testing get_comment_details...")
        print("=" * 80)
        print()
        
        # Try to find a comment for this PR from pr_comment_details table
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT comment_id 
            FROM pr_comment_details 
            WHERE pr_number = ? 
            LIMIT 1
        """, (test_pr_id,))
        
        comment_row = cursor.fetchone()
        
        if comment_row:
            test_comment_id = comment_row[0]
            print(f"Testing with comment #{test_comment_id} from PR #{test_pr_id}...")
            print()
            
            comment_details = get_comment_details(db_conn, pr_id=test_pr_id, comment_id=test_comment_id, base_dir=base_dir)
            
            if comment_details:
                print("✅ Comment Details Retrieved:")
                print("=" * 80)
                
                print(f"\n💬 COMMENT INFO:")
                print(f"  Comment ID: {comment_details['comment_id']}")
                print(f"  Type: {comment_details['comment_type']}")
                print(f"  User: {comment_details['user']}")
                print(f"  Created: {comment_details['created_at']}")
                print(f"  State: {comment_details['state']}")
                print(f"  Is Reviewer: {comment_details['is_reviewer']}")
                
                print(f"\n📍 LOCATION:")
                print(f"  Path: {comment_details.get('path', 'N/A')}")
                print(f"  Line: {comment_details.get('line', 'N/A')}")
                print(f"  Side: {comment_details.get('side', 'N/A')}")
                
                print(f"\n📦 REPOSITORY:")
                print(f"  Owner: {comment_details['owner']}")
                print(f"  Repo: {comment_details['repo']}")
                print(f"  PR Number: {comment_details['pr_number']}")
                
                print(f"\n📄 BODY:")
                body = comment_details.get('body', '')
                if body and len(str(body)) > 300:
                    print(f"  {str(body)[:300]}...")
                else:
                    print(f"  {body}")
                
                print(f"\n📁 FILE:")
                print(f"  Comments CSV: {comment_details['comments_csv_path']}")
                
                print("\n" + "=" * 80)
            else:
                print("❌ Failed to retrieve comment details")
        else:
            print("⚠️  No comments found in pr_comment_details table for this PR")
            print("   Skipping comment test")
        
        # Test get_pr_files
        print()
        print("=" * 80)
        print("Testing get_pr_files...")
        print("=" * 80)
        print()
        
        print(f"Testing with PR #{test_pr_id}...")
        print()
        
        files_list = get_pr_files(db_conn, pr_id=test_pr_id, base_dir=base_dir)
        
        if files_list:
            print(f"✅ PR Files Retrieved: {len(files_list)} file(s)")
            print("=" * 80)
            
            # Calculate totals
            total_additions = sum(f.get('additions', 0) for f in files_list)
            total_deletions = sum(f.get('deletions', 0) for f in files_list)
            total_changes = sum(f.get('changes', 0) for f in files_list)
            
            print(f"\n📊 SUMMARY:")
            print(f"  Total Files: {len(files_list)}")
            print(f"  Total Additions: +{total_additions}")
            print(f"  Total Deletions: -{total_deletions}")
            print(f"  Total Changes: {total_changes}")
            
            print(f"\n📦 REPOSITORY:")
            print(f"  Owner: {files_list[0]['owner']}")
            print(f"  Repo: {files_list[0]['repo']}")
            print(f"  PR Number: {files_list[0]['pr_number']}")
            
            print(f"\n📁 FILE:")
            print(f"  Files CSV: {files_list[0]['files_csv_path']}")
            
            # Show first 10 files
            print(f"\n📄 FILES (showing first 10 of {len(files_list)}):")
            print("-" * 80)
            for idx, file_details in enumerate(files_list[:10], 1):
                status_emoji = {
                    'added': '✨',
                    'modified': '✏️',
                    'removed': '🗑️',
                    'renamed': '📝'
                }.get(file_details.get('status', '').lower(), '📄')
                
                print(f"  {idx}. {status_emoji} {file_details['filename']}")
                print(f"     Status: {file_details['status']}")
                print(f"     Changes: +{file_details['additions']} -{file_details['deletions']} ({file_details['changes']} total)")
                
                # Print patch if available
                patch = file_details.get('patch')
                if pd.notna(patch) and patch:
                    print(f"     Patch:")
                    # Indent each line of the patch
                    for line in str(patch).split('\n'):
                        print(f"       {line}")
                else:
                    print(f"     Patch: (not available)")
                
                if idx < len(files_list[:10]):
                    print()
            
            if len(files_list) > 10:
                print(f"  ... and {len(files_list) - 10} more files")
            
            print("=" * 80)
        else:
            print("❌ Failed to retrieve PR files")
    
    db_conn.close()
    print()
    print("✅ Test complete")


if __name__ == "__main__":
    main()
