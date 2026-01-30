"""Extended tools for PR Analytics Agent - PR body, comments, files, and OKR updates."""

import sys
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3

# Add parent directory to path to import prDataReader and generateOKRUpdate
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))

from prDataReader import get_pr_details, get_comment_details, get_pr_files
from generateOKRUpdate import (
    find_prs_by_okr_and_dates,
    collect_pr_bodies,
    generate_updates_with_openai
)
from readOKRs import findByOkrName
from common import get_base_dir


def get_pr_body_tool(db_conn: sqlite3.Connection, pr_id: int, username: Optional[str] = None) -> Optional[Dict]:
    """
    Get PR body and full details from filesystem.
    
    Args:
        db_conn: Database connection
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        PR details including body, or None if not found
    """
    base_dir = get_base_dir()
    pr_details = get_pr_details(db_conn, pr_id=pr_id, username=username, base_dir=base_dir)
    return pr_details


def get_comment_body_tool(
    db_conn: sqlite3.Connection,
    pr_id: int,
    comment_id: int,
    username: Optional[str] = None
) -> Optional[Dict]:
    """
    Get specific comment details from filesystem.
    
    Args:
        db_conn: Database connection
        pr_id: PR number
        comment_id: Comment ID
        username: Optional username filter
    
    Returns:
        Comment details including body, or None if not found
    """
    base_dir = get_base_dir()
    comment_details = get_comment_details(
        db_conn,
        pr_id=pr_id,
        comment_id=comment_id,
        username=username,
        base_dir=base_dir
    )
    return comment_details


def get_pr_files_tool(db_conn: sqlite3.Connection, pr_id: int, username: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Get all files changed in a PR with patches.
    
    Args:
        db_conn: Database connection
        pr_id: PR number
        username: Optional username filter
    
    Returns:
        List of file details with patches, or None if not found
    """
    base_dir = get_base_dir()
    files_list = get_pr_files(db_conn, pr_id=pr_id, username=username, base_dir=base_dir)
    return files_list


def generate_okr_update_tool(
    db_conn: sqlite3.Connection,
    okr_search: str,
    start_date: str,
    end_date: str,
    api_key: str,
    category_search: Optional[str] = None,
    usernames: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate technical and executive updates for an OKR.
    
    Args:
        db_conn: Database connection
        okr_search: OKR search term
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        api_key: OpenAI API key
        category_search: Optional category search
        usernames: Optional list of usernames to filter
    
    Returns:
        Dict with 'technical' and 'executive' updates
    """
    base_dir = get_base_dir()
    
    # Step 1: Find OKR IDs
    okr_ids = findByOkrName(db_conn, okr_search)
    
    if not okr_ids and not category_search:
        return {
            'error': f'No OKRs found matching "{okr_search}"',
            'technical': '',
            'executive': ''
        }
    
    # Step 2: Find PRs by OKR IDs and date range
    pr_records = find_prs_by_okr_and_dates(
        db_conn,
        okr_ids,
        category_search,
        start_date,
        end_date,
        usernames
    )
    
    if not pr_records:
        return {
            'error': f'No PRs found for OKR "{okr_search}" in date range {start_date} to {end_date}',
            'technical': '',
            'executive': '',
            'pr_count': 0
        }
    
    # Step 3: Read PR bodies
    pr_details_list = collect_pr_bodies(db_conn, pr_records, base_dir)
    
    if not pr_details_list:
        return {
            'error': 'Could not read PR details from filesystem',
            'technical': '',
            'executive': '',
            'pr_count': len(pr_records)
        }
    
    # Step 4: Generate updates with OpenAI
    updates = generate_updates_with_openai(pr_details_list, okr_search, api_key)
    updates['pr_count'] = len(pr_details_list)
    updates['okr_ids'] = okr_ids
    
    return updates


def format_pr_body_response(pr_details: Dict) -> str:
    """Format PR body details for user-friendly display."""
    if not pr_details:
        return "PR not found"
    
    lines = [
        f"📝 PR #{pr_details['pr_number']}: {pr_details['pr_title']}",
        f"",
        f"👤 Author: {pr_details['pr_author']}",
        f"📦 Repo: {pr_details['repo_full']}",
        f"🔗 URL: {pr_details['pr_html_url']}",
        f"",
        f"📊 Stats:",
        f"  • State: {pr_details['pr_state']}",
        f"  • Changes: +{pr_details['pr_additions']} -{pr_details['pr_deletions']} ({pr_details['pr_changed_files']} files)",
        f"  • Comments: {pr_details['pr_issue_comments_count']} issue + {pr_details['pr_review_comments_count']} review",
        f"",
        f"📄 PR Body:",
        f"{'='*80}",
        pr_details['pr_body'] or "(No description)",
        f"{'='*80}",
    ]
    
    return "\n".join(lines)


def format_comment_response(comment_details: Dict) -> str:
    """Format comment details for user-friendly display."""
    if not comment_details:
        return "Comment not found"
    
    lines = [
        f"💬 Comment #{comment_details['comment_id']} on PR #{comment_details['pr_number']}",
        f"",
        f"👤 User: {comment_details['user']}",
        f"📅 Created: {comment_details['created_at']}",
        f"📝 Type: {comment_details['comment_type']}",
        f"🔍 State: {comment_details['state']}",
        f"",
    ]
    
    if comment_details.get('path'):
        lines.extend([
            f"📍 Location:",
            f"  • File: {comment_details['path']}",
            f"  • Line: {comment_details.get('line', 'N/A')}",
            f"  • Side: {comment_details.get('side', 'N/A')}",
            f"",
        ])
    
    lines.extend([
        f"📄 Comment Body:",
        f"{'='*80}",
        comment_details['body'] or "(No content)",
        f"{'='*80}",
    ])
    
    return "\n".join(lines)


def format_files_response(files_list: List[Dict]) -> str:
    """Format files list for user-friendly display."""
    if not files_list:
        return "No files found"
    
    # Calculate totals
    total_additions = sum(f.get('additions', 0) for f in files_list)
    total_deletions = sum(f.get('deletions', 0) for f in files_list)
    
    lines = [
        f"📊 File Changes Summary:",
        f"  • Total Files: {len(files_list)}",
        f"  • Total Additions: +{total_additions}",
        f"  • Total Deletions: -{total_deletions}",
        f"",
        f"📁 Files:",
        f"{'='*80}",
    ]
    
    for idx, file in enumerate(files_list, 1):
        status_emoji = {
            'added': '✨',
            'modified': '✏️',
            'removed': '🗑️',
            'renamed': '📝'
        }.get(file.get('status', '').lower(), '📄')
        
        lines.extend([
            f"{idx}. {status_emoji} {file['filename']}",
            f"   Status: {file['status']}",
            f"   Changes: +{file['additions']} -{file['deletions']} ({file['changes']} total)",
        ])
        
        # Show patch snippet if available
        patch = file.get('patch')
        if patch and str(patch) != 'nan':
            patch_str = str(patch)
            if len(patch_str) > 200:
                lines.append(f"   Patch: {patch_str[:200]}...")
            else:
                lines.append(f"   Patch: {patch_str}")
        
        lines.append("")
    
    lines.append("="*80)
    return "\n".join(lines)


def format_okr_update_response(updates: Dict) -> str:
    """Format OKR update for user-friendly display."""
    if updates.get('error'):
        return f"❌ Error: {updates['error']}"
    
    lines = [
        f"📊 OKR Update Generated",
        f"  • PRs Analyzed: {updates.get('pr_count', 0)}",
        f"  • OKR IDs: {updates.get('okr_ids', [])}",
        f"",
        f"{'='*80}",
        f"🔧 TECHNICAL UPDATE ({len(updates.get('technical', ''))} chars)",
        f"{'='*80}",
        updates.get('technical', ''),
        f"",
        f"{'='*80}",
        f"👔 EXECUTIVE UPDATE ({len(updates.get('executive', ''))} chars)",
        f"{'='*80}",
        updates.get('executive', ''),
        f"",
        f"{'='*80}",
    ]
    
    return "\n".join(lines)
