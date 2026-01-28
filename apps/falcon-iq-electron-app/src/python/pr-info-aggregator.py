#!/usr/bin/env python3
"""
PR Information Aggregator

Aggregates PR information for each user combining:
- PR authored data
- PR reviewed data
- OKR mappings
- Metadata (created time, author, repo, confidence)

Prerequisites:
- OKR mapping must be completed (Step 5: prOKRMapper.py)

Output: pr_data_folder/pr-stats/pr_{username}_{start_date}_{end_date}.csv

Columns:
- username: User's username
- pr_id: PR number
- okr: Mapped OKR (if available)
- created_time: PR creation timestamp
- confidence: OKR mapping confidence score
- reviewed_authored: "authored" or "reviewed"
- author_of_pr: PR author's username
- repo: Repository name
- is-ai-author: Boolean indicating if PR author is an AI/bot

Usage:
    python pr-info-aggregator.py
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
from common import load_all_config


def check_okr_mapping_completed(task_folder: Path, username: str) -> bool:
    """
    Check if OKR mapping is completed for a user.
    Requires BOTH authored and reviewer OKR status files to be completed.
    
    Args:
        task_folder: Path to task folder
        username: Username
    
    Returns:
        True if OKR mapping is completed for BOTH authored and reviewer, False otherwise
    """
    # Check for OKR mapping status files
    task_types = ["authored", "reviewer"]
    completed_count = 0
    
    for task_type in task_types:
        okr_status_file = task_folder / f"pr_{task_type}_okr_{username}_status.json"
        
        if not okr_status_file.exists():
            return False  # Missing status file
        
        try:
            with open(okr_status_file, 'r') as f:
                status_data = json.load(f)
            
            if status_data.get('status') == 'completed':
                completed_count += 1
        except Exception:
            return False  # Error reading file
    
    # Both must be completed
    return completed_count == 2


def is_ai_author(username: str, ai_reviewer_prefixes: List[str]) -> bool:
    """
    Check if username matches AI reviewer prefixes.
    
    Args:
        username: Username to check
        ai_reviewer_prefixes: List of AI reviewer prefixes
    
    Returns:
        True if username starts with any AI prefix, False otherwise
    """
    if not username or not ai_reviewer_prefixes:
        return False
    username_lower = str(username).lower()
    return any(username_lower.startswith(prefix.lower()) for prefix in ai_reviewer_prefixes)


def load_pr_author(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> str:
    """
    Load PR author from pr metadata file.
    
    Args:
        pr_data_folder: PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        PR author username or empty string if not found
    """
    meta_file = pr_data_folder / owner / repo / f"pr_{pr_number}" / f"pr_{pr_number}_meta.csv"
    
    if not meta_file.exists():
        return ''
    
    try:
        meta_df = pd.read_csv(meta_file)
        if len(meta_df) > 0 and 'pr_author' in meta_df.columns:
            author = meta_df.iloc[0]['pr_author']
            return str(author) if author and not pd.isna(author) else ''
    except Exception:
        pass
    
    return ''


def load_pr_okr(pr_data_folder: Path, owner: str, repo: str, pr_number: int, username: str) -> tuple[str, str]:
    """
    Load OKR data from PR folder.
    
    Args:
        pr_data_folder: PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        username: User's username
    
    Returns:
        Tuple of (okr, confidence) - okr is okr_text or category, confidence is float
    """
    okr_file = pr_data_folder / owner / repo / f"pr_{pr_number}" / f"okrs_{username}.csv"
    
    if not okr_file.exists():
        return '', ''
    
    try:
        okr_df = pd.read_csv(okr_file)
        if len(okr_df) > 0:
            # Get first row (highest confidence match)
            row = okr_df.iloc[0]
            
            # Try to get okr_text first, fallback to category
            okr = row.get('okr_text', '')
            if not okr or pd.isna(okr) or okr == '':
                category = row.get('category', '')
                if category and not pd.isna(category):
                    okr = f"[{category}]"
            
            # Get confidence
            confidence = row.get('confidence', '')
            if confidence and not pd.isna(confidence):
                confidence = str(confidence)
            else:
                confidence = ''
            
            return okr, confidence
    except Exception as e:
        pass
    
    return '', ''


def process_pr_file(pr_file: Path, file_type: str, username: str, 
                   pr_data_folder: Path, ai_reviewer_prefixes: List[str]) -> pd.DataFrame:
    """
    Process a single PR file (authored or reviewed).
    
    Args:
        pr_file: Path to PR CSV file
        file_type: "authored" or "reviewed"
        username: User's username
        pr_data_folder: PR data folder path
        ai_reviewer_prefixes: List of AI reviewer prefixes
    
    Returns:
        DataFrame with processed PR statistics
    """
    if not pr_file.exists():
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(pr_file)
    except Exception as e:
        print(f"      ⚠️  Error loading PR file: {e}")
        return pd.DataFrame()
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Initialize result list
    results = []
    
    for idx, row in df.iterrows():
        pr_number = row.get('pr_number', row.get('number', None))
        owner = row.get('owner', '')
        repo = row.get('repo', '')
        created_at = row.get('created_at', '')
        
        # Load PR author from metadata file
        author = ''
        if pr_number and owner and repo:
            author = load_pr_author(pr_data_folder, owner, repo, pr_number)
        
        # Load OKR from PR folder
        okr = ''
        confidence = ''
        if pr_number and owner and repo:
            okr, confidence = load_pr_okr(pr_data_folder, owner, repo, pr_number, username)
        
        # Check if author is AI
        is_ai = is_ai_author(author, ai_reviewer_prefixes) if author else False
        
        # Create result row
        result = {
            'username': username,
            'pr_id': pr_number,
            'okr': okr if okr and not pd.isna(okr) else '',
            'created_time': created_at,
            'confidence': confidence if confidence and not pd.isna(confidence) else '',
            'reviewed_authored': file_type,
            'author_of_pr': author,
            'repo': f"{owner}/{repo}" if owner and repo else repo,
            'is-ai-author': is_ai
        }
        
        results.append(result)
    
    return pd.DataFrame(results)


def generate_stats_for_user(username: str, base_dir: Path, pr_data_folder: Path, 
                            task_folder: Path, stats_folder: Path, 
                            ai_reviewer_prefixes: List[str]) -> bool:
    """
    Generate PR statistics for a single user.
    
    Args:
        username: User's username
        base_dir: Base directory path
        pr_data_folder: PR data folder path
        task_folder: Task folder path
        stats_folder: Output stats folder path
    
    Returns:
        True if successful, False otherwise
    """
    print(f"\n{'='*80}")
    print(f"👤 User: {username}")
    print(f"{'='*80}")
    
    # Check if OKR mapping is completed
    if not check_okr_mapping_completed(task_folder, username):
        print(f"   ⚠️  OKR mapping not completed for {username}")
        print(f"   ℹ️  Run Step 5 (prOKRMapper.py) first")
        return False
    
    print(f"   ✅ OKR mapping completed")
    
    # Read task files to get date ranges
    task_types = ["authored", "reviewer"]
    all_stats = []
    start_date = None
    end_date = None
    
    for task_type in task_types:
        task_file = task_folder / f"pr_{task_type}_{username}.json"
        
        if not task_file.exists():
            print(f"   ⚠️  Task file not found: {task_file.name}")
            continue
        
        try:
            with open(task_file, 'r') as f:
                task_data = json.load(f)
            
            task_start = task_data.get('start_date')
            task_end = task_data.get('end_date')
            
            if not task_start or not task_end:
                print(f"   ⚠️  Missing date range in {task_file.name}")
                continue
            
            # Use the first date range found
            if not start_date:
                start_date = task_start
                end_date = task_end
            
            print(f"   ✅ Task file: {task_file.name}")
            print(f"   📅 Date range: {task_start} to {task_end}")
            
            # Construct PR file path
            pr_filename = f"pr_{task_type}_{username}_{task_start}_{task_end}.csv"
            pr_file = pr_data_folder / "search" / pr_filename
            
            if not pr_file.exists():
                print(f"   ⚠️  PR file not found: {pr_filename}")
                continue
            
            print(f"   📄 Processing: {pr_filename}")
            
            # Determine file type for output
            file_type = "authored" if task_type == "authored" else "reviewed"
            
            # Process PR file (OKRs are loaded from individual PR folders)
            stats_df = process_pr_file(pr_file, file_type, username, pr_data_folder, 
                                      ai_reviewer_prefixes)
            
            if len(stats_df) > 0:
                all_stats.append(stats_df)
                print(f"   ✅ Processed {len(stats_df)} PRs from {pr_filename}")
            else:
                print(f"   ℹ️  No PRs found in {pr_filename}")
        
        except Exception as e:
            print(f"   ❌ Error processing {task_file.name}: {e}")
            continue
    
    # Combine all stats
    if not all_stats:
        print(f"   ⚠️  No PR data found for {username}")
        return False
    
    if not start_date or not end_date:
        print(f"   ⚠️  No date range found for {username}")
        return False
    
    combined_stats = pd.concat(all_stats, ignore_index=True)
    
    # Create output file
    output_file = stats_folder / f"pr_{username}_{start_date}_{end_date}.csv"
    
    # Save to CSV
    combined_stats.to_csv(output_file, index=False)
    
    print(f"\n   📊 Statistics Summary:")
    print(f"      Total PRs: {len(combined_stats)}")
    print(f"      Authored: {len(combined_stats[combined_stats['reviewed_authored'] == 'authored'])}")
    print(f"      Reviewed: {len(combined_stats[combined_stats['reviewed_authored'] == 'reviewed'])}")
    print(f"      With OKRs: {len(combined_stats[combined_stats['okr'] != ''])}")
    print(f"   💾 Saved to: {output_file.name}")
    
    return True


def main():
    """Main function"""
    print("=" * 80)
    print("PR Information Aggregator")
    print("=" * 80)
    print()
    print("⚠️  Prerequisites: OKR mapping must be completed (Step 5)")
    print()
    
    # Load all configuration
    all_config = load_all_config()
    config = all_config['config']
    settings = all_config['settings']
    users = all_config['users']
    paths = all_config['paths']
    
    base_dir = paths['base_dir']
    pr_data_folder = paths['pr_data_folder']
    task_folder = base_dir / config.get('task_folder', 'pipeline-tasks')
    stats_folder = pr_data_folder / "pr-stats"
    
    # Get AI reviewer prefixes from settings
    ai_reviewer_prefixes = settings.get('ai_reviewer_prefixes', ["github-actions", "svc-gha"])
    
    print(f"📁 Base directory: {base_dir}")
    print(f"📂 PR data folder: {pr_data_folder}")
    print(f"📂 Task folder: {task_folder}")
    print(f"📂 Stats folder: {stats_folder}")
    print(f"🤖 AI reviewer prefixes: {ai_reviewer_prefixes}")
    print()
    
    # Create stats folder if it doesn't exist
    stats_folder.mkdir(parents=True, exist_ok=True)
    print(f"✅ Stats folder ready: {stats_folder}")
    
    print(f"👥 Found {len(users)} users")
    print()
    
    # Process each user
    total_users = len(users)
    successful = 0
    failed = 0
    skipped = 0
    
    for idx, user in enumerate(users, 1):
        username = user.get('userName')
        if not username:
            print(f"⚠️  Skipping user with no userName")
            failed += 1
            continue
        
        try:
            success = generate_stats_for_user(
                username, base_dir, pr_data_folder, task_folder, stats_folder, ai_reviewer_prefixes
            )
            
            if success:
                successful += 1
            else:
                # Check if it was skipped due to incomplete OKR mapping
                if not check_okr_mapping_completed(task_folder, username):
                    skipped += 1
                else:
                    failed += 1
        
        except Exception as e:
            failed += 1
            print(f"\n   ❌ Error processing {username}: {e}")
    
    # Final summary
    print(f"\n{'='*80}")
    print("📊 Aggregation Summary")
    print(f"{'='*80}")
    print(f"✅ Successful: {successful}")
    print(f"⏭️  Skipped (OKR mapping incomplete): {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {total_users}")
    print()


if __name__ == "__main__":
    main()
