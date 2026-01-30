#!/usr/bin/env python3
"""
Generate OKR Updates from PR Data

Finds PRs related to an OKR (by name or category) within a date range,
reads PR bodies, and generates technical and executive summaries using OpenAI.

Usage:
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31"
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31" --base-dir ~/path
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31" --usernames user1 user2

Examples:
    # Generate update for resiliency OKR in Q1 2024
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31"
    
    # Use custom base directory
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31" --base-dir ~/Library/Application\ Support/Falcon\ IQ
    
    # Filter by specific users
    python generateOKRUpdate.py --okr-search "resiliency" --start-date "2024-01-01" --end-date "2024-03-31" --usernames npurwar jsmith
    
    # Combine filters
    python generateOKRUpdate.py --okr-search "infrastructure" --start-date "2024-01-01" --end-date "2024-03-31" --usernames npurwar --category-search "reliability"
"""

import sqlite3
import argparse
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from openai import OpenAI

from common import get_base_dir, getDBPath, set_base_dir, load_user_settings, get_openai_api_key
from readOKRs import connect_to_database, findByOkrName
from prDataReader import get_pr_details


def find_prs_by_okr_and_dates(
    conn: sqlite3.Connection,
    okr_ids: List[int],
    category_search: Optional[str],
    start_date: str,
    end_date: str,
    usernames: Optional[List[str]] = None
) -> List[Dict]:
    """
    Find PRs from pr_stats table filtered by goal IDs or category and date range.
    
    Args:
        conn: Database connection
        okr_ids: List of goal/OKR IDs to filter by
        category_search: Optional category search term (LIKE query)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        usernames: Optional list of usernames to filter by
    
    Returns:
        List of PR records with pr_id, username, category, created_time, etc.
    """
    cursor = conn.cursor()
    
    # Build query with filters
    query_parts = ["SELECT pr_id, username, category, created_time, repo FROM pr_stats WHERE 1=1"]
    params = []
    
    # Add goal ID filter (if provided)
    if okr_ids:
        placeholders = ','.join('?' * len(okr_ids))
        query_parts.append(f"AND goal_id IN ({placeholders})")
        params.extend(okr_ids)
    
    # Add category filter (if provided and no OKR IDs)
    if category_search and not okr_ids:
        query_parts.append("AND category LIKE ?")
        params.append(f"%{category_search}%")
    
    # Add username filter (if provided)
    if usernames:
        placeholders = ','.join('?' * len(usernames))
        query_parts.append(f"AND username IN ({placeholders})")
        params.extend(usernames)
    
    # Add date range filter (created_time)
    query_parts.append("AND created_time >= ? AND created_time <= ?")
    params.append(start_date)
    params.append(end_date)
    
    # Order by created date
    query_parts.append("ORDER BY created_time DESC")
    
    query = " ".join(query_parts)
    
    print(f"\n🔍 Executing query:")
    print(f"   {query}")
    print(f"   Params: {params}")
    print()
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    prs = []
    for row in rows:
        pr = {
            'pr_id': row['pr_id'],
            'username': row['username'],
            'category': row['category'],
            'created_time': row['created_time'],
            'repo': row['repo']
        }
        prs.append(pr)
    
    return prs


def collect_pr_bodies(conn: sqlite3.Connection, pr_records: List[Dict], base_dir: Path) -> List[Dict]:
    """
    Read PR bodies from filesystem for each PR record.
    
    Args:
        conn: Database connection
        pr_records: List of PR records from pr_stats
        base_dir: Base directory path
    
    Returns:
        List of PR details with bodies
    """
    pr_details_list = []
    
    print(f"\n📄 Reading PR details from filesystem...")
    print("=" * 80)
    
    for idx, pr_record in enumerate(pr_records, 1):
        pr_id = pr_record['pr_id']
        username = pr_record['username']
        
        print(f"  {idx}. PR #{pr_id} (user: {username})")
        
        try:
            pr_details = get_pr_details(
                db_conn=conn,
                pr_id=pr_id,
                username=username,
                base_dir=base_dir
            )
            
            if pr_details:
                # Add metadata from pr_stats
                pr_details['category_from_stats'] = pr_record.get('category')
                pr_details['created_time_from_stats'] = pr_record.get('created_time')
                pr_details_list.append(pr_details)
                print(f"      ✅ Read PR body ({len(pr_details.get('pr_body', ''))} chars)")
            else:
                print(f"      ⚠️  Could not read PR details")
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    print("=" * 80)
    return pr_details_list


def generate_updates_with_openai(pr_details_list: List[Dict], okr_search: str, api_key: str) -> Dict[str, str]:
    """
    Generate technical and executive updates using OpenAI.
    
    Args:
        pr_details_list: List of PR details with bodies
        okr_search: OKR search term for context
        api_key: OpenAI API key
    
    Returns:
        Dictionary with 'technical' and 'executive' updates
    """
    # Prepare context from PR bodies
    pr_summaries = []
    for pr in pr_details_list:
        pr_summary = f"""
PR #{pr['pr_number']}: {pr['pr_title']}
Author: {pr['pr_author']}
Created: {pr.get('created_time_from_stats', pr.get('pr_created_at', 'N/A'))}
Merged: {pr.get('pr_merged_at', 'N/A')}
Category: {pr.get('category_from_stats', 'N/A')}
Repo: {pr['repo_full']}
Body: {pr['pr_body'][:1000]}...
---
"""
        pr_summaries.append(pr_summary)
    
    context = "\n".join(pr_summaries)
    
    print(f"\n🤖 Generating updates with OpenAI...")
    print(f"   Context: {len(pr_details_list)} PRs, {len(context)} chars")
    print()
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    
    # Generate technical update (1000 chars)
    technical_prompt = f"""You are a technical program manager. Based on the following pull requests related to the OKR/goal "{okr_search}", generate a concise technical update.

Requirements:
- Maximum 1000 characters
- Focus on technical details, implementations, and changes
- Use bullet points for clarity
- Include PR numbers when referencing specific changes
- Be specific about what was accomplished

Pull Requests:
{context}

Generate a technical update:"""
    
    print("📝 Generating technical update...")
    technical_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a technical program manager who writes concise, clear technical updates."},
            {"role": "user", "content": technical_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )
    technical_update = technical_response.choices[0].message.content.strip()
    
    # Generate executive update (2000 chars)
    executive_prompt = f"""You are an executive program manager. Based on the following pull requests related to the OKR/goal "{okr_search}", generate a comprehensive executive summary.

Requirements:
- Maximum 2000 characters
- Focus on business impact, outcomes, and strategic alignment
- Use clear, non-technical language
- Highlight key achievements and their impact
- Include metrics where relevant
- Be concise but comprehensive

Pull Requests:
{context}

Generate an executive update:"""
    
    print("📝 Generating executive update...")
    executive_response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an executive program manager who writes clear, impactful executive summaries."},
            {"role": "user", "content": executive_prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    executive_update = executive_response.choices[0].message.content.strip()
    
    return {
        'technical': technical_update,
        'executive': executive_update
    }


def print_updates(updates: Dict[str, str], pr_count: int, okr_search: str, start_date: str, end_date: str):
    """Print the generated updates in a formatted way."""
    print("\n" + "=" * 80)
    print("📊 OKR UPDATE GENERATED")
    print("=" * 80)
    print()
    print(f"🎯 OKR: {okr_search}")
    print(f"📅 Period: {start_date} to {end_date}")
    print(f"📝 PRs Analyzed: {pr_count}")
    print()
    
    print("=" * 80)
    print("🔧 TECHNICAL UPDATE (1000 chars max)")
    print("=" * 80)
    print()
    print(updates['technical'])
    print()
    print(f"Character count: {len(updates['technical'])}")
    print()
    
    print("=" * 80)
    print("👔 EXECUTIVE UPDATE (2000 chars max)")
    print("=" * 80)
    print()
    print(updates['executive'])
    print()
    print(f"Character count: {len(updates['executive'])}")
    print()
    print("=" * 80)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate OKR updates from PR data using OpenAI'
    )
    parser.add_argument(
        '--okr-search',
        type=str,
        required=True,
        help='Search term to find OKRs by name (case-insensitive, partial match)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        required=True,
        help='Start date for PR filter - filters by created_time (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        required=True,
        help='End date for PR filter - filters by created_time (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        help='Base directory path (overrides FALCON_BASE_DIR env var and config)'
    )
    parser.add_argument(
        '--category-search',
        type=str,
        help='Optional: Search term for category field (used if no OKRs found)'
    )
    parser.add_argument(
        '--usernames',
        type=str,
        nargs='+',
        help='Optional: Filter by specific username(s). Can provide multiple: --usernames user1 user2 user3'
    )
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.start_date, '%Y-%m-%d')
        datetime.strptime(args.end_date, '%Y-%m-%d')
    except ValueError as e:
        print(f"❌ Invalid date format: {e}")
        print("   Please use YYYY-MM-DD format (e.g., 2024-01-01)")
        return
    
    # Set base directory if provided
    if args.base_dir:
        base_dir_path = Path(args.base_dir).expanduser()
        set_base_dir(str(base_dir_path))
        print(f"📁 Using base directory: {base_dir_path}")
        print()
    
    print("🚀 OKR Update Generator")
    print("=" * 80)
    print(f"🎯 OKR Search: {args.okr_search}")
    print(f"📅 Date Range: {args.start_date} to {args.end_date}")
    if args.category_search:
        print(f"🏷️  Category Search: {args.category_search}")
    if args.usernames:
        print(f"👥 Filter by Users: {', '.join(args.usernames)}")
    print("=" * 80)
    print()
    
    # Get base directory and database
    base_dir = get_base_dir()
    db_path = getDBPath(base_dir)
    
    # Get OpenAI API key
    settings = load_user_settings(base_dir)
    api_key = get_openai_api_key(settings)
    if not api_key:
        api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("   Please set it in settings file or OPENAI_API_KEY environment variable")
        return
    
    # Connect to database
    conn = connect_to_database(db_path, quiet=False)
    if not conn:
        return
    
    # Step 1: Find OKR IDs by name
    print(f"\n📍 Step 1: Finding OKRs matching '{args.okr_search}'...")
    okr_ids = findByOkrName(conn, args.okr_search)
    print(f"   Found {len(okr_ids)} OKR ID(s): {okr_ids}")
    
    # Step 2: Find PRs by OKR IDs and date range
    print(f"\n📍 Step 2: Finding PRs in date range...")
    pr_records = find_prs_by_okr_and_dates(
        conn,
        okr_ids,
        args.category_search,
        args.start_date,
        args.end_date,
        args.usernames
    )
    print(f"   Found {len(pr_records)} PR(s)")
    
    if not pr_records:
        print("\n⚠️  No PRs found for the given criteria")
        conn.close()
        return
    
    # Step 3: Read PR bodies from filesystem
    print(f"\n📍 Step 3: Reading PR details from filesystem...")
    pr_details_list = collect_pr_bodies(conn, pr_records, base_dir)
    print(f"   Successfully read {len(pr_details_list)} PR detail(s)")
    
    if not pr_details_list:
        print("\n⚠️  Could not read any PR details from filesystem")
        conn.close()
        return
    
    # Step 4: Generate updates with OpenAI
    print(f"\n📍 Step 4: Generating updates with OpenAI...")
    updates = generate_updates_with_openai(pr_details_list, args.okr_search, api_key)
    
    # Close database connection
    conn.close()
    
    # Print updates
    print_updates(updates, len(pr_details_list), args.okr_search, args.start_date, args.end_date)
    
    print("✅ Update generation complete!")


if __name__ == "__main__":
    main()
