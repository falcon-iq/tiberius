#!/usr/bin/env python3
"""
PR Comment File Generator

Generates comment CSV files for each user by extracting all comments from reviewed PRs.
Creates files in format: username_comments_start-date_end-date.csv
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List
from common import load_all_config


def load_pr_comments(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> pd.DataFrame:
    """
    Load comments for a specific PR.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        DataFrame with comments or empty DataFrame if not found
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    comments_path = pr_dir / f"pr_{pr_number}_comments.csv"
    meta_path = pr_dir / f"pr_{pr_number}_meta.csv"
    
    if not comments_path.exists():
        return pd.DataFrame()
    
    try:
        comments_df = pd.read_csv(comments_path)
        
        # Get PR author from metadata
        pr_author = "unknown"
        pr_title = ""
        pr_html_url = ""
        
        if meta_path.exists():
            try:
                meta_df = pd.read_csv(meta_path)
                if len(meta_df) > 0:
                    pr_author = meta_df.iloc[0].get("pr_author", "unknown")
                    pr_title = meta_df.iloc[0].get("pr_title", "")
                    pr_html_url = meta_df.iloc[0].get("pr_html_url", "")
            except Exception:
                pass
        
        # Add PR context to each comment
        comments_df["owner"] = owner
        comments_df["repo"] = repo
        comments_df["pr_number"] = pr_number
        comments_df["pr_author"] = pr_author
        comments_df["pr_title"] = pr_title
        comments_df["pr_html_url"] = pr_html_url
        
        return comments_df
    except Exception as e:
        print(f"         ⚠️  Error reading comments for PR #{pr_number}: {e}")
        return pd.DataFrame()


def generate_comments_for_user_combined(username: str, pr_username: str, authored_pr_index: Path,
                                        reviewed_pr_index: Path, pr_data_folder: Path, 
                                        output_folder: Path, start_date: str, end_date: str) -> bool:
    """
    Generate two comment CSV files for a specific user:
    1. All comments on PRs authored by the user (from everyone)
    2. Comments by the user on PRs authored by others
    
    Args:
        username: Username for file naming
        pr_username: Username as it appears in PR comments (from prUserName field in users.json)
        authored_pr_index: Path to authored PR index CSV
        reviewed_pr_index: Path to reviewed PR index CSV
        pr_data_folder: Base PR data folder path
        output_folder: Folder to save output CSV
        start_date: Start date from task
        end_date: End date from task
    
    Returns:
        True if successful, False otherwise
    """
    # Output files
    authored_comments_file = output_folder / f"{username}_comments_on_authored_prs_{start_date}_{end_date}.csv"
    reviewed_comments_file = output_folder / f"{username}_comments_on_reviewed_prs_{start_date}_{end_date}.csv"
    
    # Check if output files already exist
    if authored_comments_file.exists() and reviewed_comments_file.exists():
        print(f"      ✅ Comments files already exist")
        print(f"         - {authored_comments_file.name}")
        print(f"         - {reviewed_comments_file.name}")
        return True
    
    try:
        # ========================================
        # PART 1: Comments on AUTHORED PRs (all comments from everyone)
        # ========================================
        authored_all_comments = []
        authored_prs_processed = 0
        
        if authored_pr_index and authored_pr_index.exists():
            authored_prs_df = pd.read_csv(authored_pr_index)
            print(f"      📝 Processing {len(authored_prs_df)} authored PRs...")
            
            for idx, row in authored_prs_df.iterrows():
                owner = str(row["owner"]).strip()
                repo = str(row["repo"]).strip()
                pr_number = int(row["pr_number"])
                
                comments_df = load_pr_comments(pr_data_folder, owner, repo, pr_number)
                if len(comments_df) > 0:
                    authored_all_comments.append(comments_df)
                    authored_prs_processed += 1
        
        # Save all comments on authored PRs
        if authored_all_comments:
            authored_comments_df = pd.concat(authored_all_comments, ignore_index=True)
            print(f"      📊 Total comments on authored PRs: {len(authored_comments_df)} (from {authored_prs_processed} PRs)")
            
            # Show unique commenters
            unique_commenters = authored_comments_df["user"].dropna().unique()
            print(f"      👥 Commenters: {len(unique_commenters)} users")
            
            authored_comments_df.to_csv(authored_comments_file, index=False)
            print(f"      ✅ Saved authored PR comments to: {authored_comments_file.name}")
        else:
            print(f"      ℹ️  No comments on authored PRs - creating empty file")
            pd.DataFrame().to_csv(authored_comments_file, index=False)
        
        # ========================================
        # PART 2: User's comments on REVIEWED PRs (only by this user)
        # ========================================
        reviewed_user_comments = []
        reviewed_prs_processed = 0
        
        if reviewed_pr_index and reviewed_pr_index.exists():
            reviewed_prs_df = pd.read_csv(reviewed_pr_index)
            print(f"\n      📝 Processing {len(reviewed_prs_df)} reviewed PRs...")
            
            for idx, row in reviewed_prs_df.iterrows():
                owner = str(row["owner"]).strip()
                repo = str(row["repo"]).strip()
                pr_number = int(row["pr_number"])
                
                comments_df = load_pr_comments(pr_data_folder, owner, repo, pr_number)
                if len(comments_df) > 0:
                    # Filter to only this user's comments
                    user_comments = comments_df[comments_df["user"] == pr_username]
                    if len(user_comments) > 0:
                        reviewed_user_comments.append(user_comments)
                        reviewed_prs_processed += 1
        
        # Save user's comments on reviewed PRs
        if reviewed_user_comments:
            reviewed_comments_df = pd.concat(reviewed_user_comments, ignore_index=True)
            print(f"      📊 Comments by {pr_username} on reviewed PRs: {len(reviewed_comments_df)} (from {reviewed_prs_processed} PRs)")
            
            if "comment_type" in reviewed_comments_df.columns:
                comment_types = reviewed_comments_df["comment_type"].value_counts().to_dict()
                print(f"      📋 Comment types: {comment_types}")
            
            reviewed_comments_df.to_csv(reviewed_comments_file, index=False)
            print(f"      ✅ Saved reviewed PR comments to: {reviewed_comments_file.name}")
        else:
            print(f"      ℹ️  No comments by {pr_username} on reviewed PRs - creating empty file")
            pd.DataFrame().to_csv(reviewed_comments_file, index=False)
        
        print(f"\n      🎯 Summary:")
        print(f"         - Authored PRs: ALL comments from everyone")
        print(f"         - Reviewed PRs: Only {pr_username}'s comments")
        
        return True
    
    except Exception as e:
        print(f"      ❌ Error generating comments: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_comments_for_user(username: str, pr_index_file: Path, pr_data_folder: Path, 
                               output_folder: Path, start_date: str, end_date: str) -> bool:
    """
    Generate comments CSV file for a specific user.
    
    Args:
        username: Username to generate comments for
        pr_index_file: Path to PR index CSV (reviewed PRs)
        pr_data_folder: Base PR data folder path
        output_folder: Folder to save output CSV
        start_date: Start date from task
        end_date: End date from task
    
    Returns:
        True if successful, False otherwise
    """
    # Check if output file already exists
    output_file = output_folder / f"{username}_comments_{start_date}_{end_date}.csv"
    
    if output_file.exists():
        print(f"      ✅ Comments file already exists: {output_file.name}")
        return True
    
    # Check if PR index exists
    if not pr_index_file.exists():
        print(f"      ⚠️  PR index not found: {pr_index_file}")
        return False
    
    try:
        # Load PR index
        prs_df = pd.read_csv(pr_index_file)
        print(f"      📄 Found {len(prs_df)} reviewed PRs in index")
        
        if len(prs_df) == 0:
            print(f"      ℹ️  No PRs to process - creating empty file")
            pd.DataFrame().to_csv(output_file, index=False)
            return True
        
        # Load comments for all PRs
        all_comments = []
        prs_processed = 0
        
        for idx, row in prs_df.iterrows():
            owner = str(row["owner"]).strip()
            repo = str(row["repo"]).strip()
            pr_number = int(row["pr_number"])
            
            comments_df = load_pr_comments(pr_data_folder, owner, repo, pr_number)
            if len(comments_df) > 0:
                all_comments.append(comments_df)
                prs_processed += 1
        
        # Combine all comments
        if all_comments:
            all_comments_df = pd.concat(all_comments, ignore_index=True)
            print(f"      📊 Total comments across {prs_processed} PRs: {len(all_comments_df)}")
            
            # Debug: Show unique users in comments
            unique_users = all_comments_df["user"].dropna().unique()
            print(f"      👥 Unique commenters ({len(unique_users)}): {', '.join(sorted(unique_users)[:10])}")
            if len(unique_users) > 10:
                print(f"         ... and {len(unique_users) - 10} more")
            
            # Debug: Check username matching
            print(f"\n      🔍 Looking for comments by: '{pr_username}'")
            exact_match_count = (all_comments_df["user"] == pr_username).sum()
            print(f"         Exact match count: {exact_match_count}")
            
            # Show sample comments with users
            print(f"         Sample comments (first 5):")
            sample_cols = ["user", "pr_number", "pr_author", "comment_type"]
            available_cols = [c for c in sample_cols if c in all_comments_df.columns]
            print(all_comments_df[available_cols].head(5).to_string(index=False))
            
            # Check for similar usernames if no exact match
            if exact_match_count == 0:
                similar_users = [u for u in unique_users if username.lower() in str(u).lower()]
                if similar_users:
                    print(f"         ⚠️  No exact match. Similar usernames found: {similar_users}")
                    print(f"             Add 'prUserName' field in users.json")
            
            # Filter comments by the PR username
            user_comments = all_comments_df[all_comments_df["user"] == pr_username].copy()
            print(f"\n      💬 Comments by {pr_username}: {len(user_comments)}")
            
            if len(user_comments) > 0:
                print(f"      📝 PRs with comments by {pr_username}: {user_comments['pr_number'].nunique()}")
                if "comment_type" in user_comments.columns:
                    comment_types = user_comments["comment_type"].value_counts().to_dict()
                    print(f"      📋 Comment types: {comment_types}")
            
            # Save user-specific comments to CSV (even if empty)
            user_comments.to_csv(output_file, index=False)
            print(f"      ✅ Saved user comments to: {output_file.name}")
            if len(user_comments) > 0:
                print(f"         Columns: {', '.join(user_comments.columns.tolist())}")
            
            return True
        else:
            print(f"      ℹ️  No comments found - creating empty file")
            pd.DataFrame().to_csv(output_file, index=False)
            return True
    
    except Exception as e:
        print(f"      ❌ Error generating comments: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("💬 PR COMMENT FILE GENERATOR")
        print("=" * 80)
        print()
        
        # Load configuration
        print("🔄 Loading configuration...")
        all_config = load_all_config()
        
        config = all_config['config']
        settings = all_config['settings']
        users = all_config['users']
        paths = all_config['paths']
        
        task_folder = paths['task_folder']
        pr_data_folder = paths['pr_data_folder']
        search_folder = pr_data_folder / 'search'
        
        # Create comments output folder
        comments_folder = pr_data_folder / 'comments'
        comments_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"✅ Configuration loaded")
        print(f"   Task folder: {task_folder}")
        print(f"   PR data folder: {pr_data_folder}")
        print(f"   Search folder: {search_folder}")
        print(f"   Comments folder: {comments_folder}")
        print(f"   Users: {len(users)}")
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("🔄 GENERATING COMMENT FILES FOR USERS")
        print("=" * 80)
        
        task_types = ["authored", "reviewer"]  # Look at both authored AND reviewed PRs
        total_generated = 0
        total_skipped = 0
        total_failed = 0
        
        for user in users:
            username = user['userName']
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            # Get PR username (for comment filtering) from prUserName field in users.json
            pr_username = user.get('prUserName', username)
            
            print(f"\n👤 User: {full_name} ({username})")
            if pr_username != username:
                print(f"   PR Username: {pr_username}")
            print("-" * 80)
            
            # Get authored and reviewed PR indices separately
            authored_pr_index = None
            reviewed_pr_index = None
            start_date = None
            end_date = None
            
            for task_type in task_types:
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                if not task_filepath.exists():
                    print(f"   ⚠️  Task file not found: {task_filename}")
                    continue
                
                try:
                    # Read task file to get date range
                    with open(task_filepath, 'r') as f:
                        task_data = json.load(f)
                    
                    task_start_date = task_data.get('start_date')
                    task_end_date = task_data.get('end_date')
                    
                    if not task_start_date or not task_end_date:
                        print(f"   ⚠️  Missing date range in {task_filename}")
                        continue
                    
                    # Use the date range from the first valid task
                    if not start_date:
                        start_date = task_start_date
                        end_date = task_end_date
                    
                    print(f"   ✅ Task file: {task_filename}")
                    print(f"   📅 Date range: {task_start_date} to {task_end_date}")
                    
                    # Get PR index file
                    pr_index_filename = f"pr_{task_type}_{username}_{task_start_date}_{task_end_date}.csv"
                    pr_index_filepath = search_folder / pr_index_filename
                    
                    if pr_index_filepath.exists():
                        if task_type == "authored":
                            authored_pr_index = pr_index_filepath
                        elif task_type == "reviewer":
                            reviewed_pr_index = pr_index_filepath
                        print(f"   ✅ PR index found: {pr_index_filename}")
                    else:
                        print(f"   ⚠️  PR index not found: {pr_index_filename}")
                
                except Exception as e:
                    print(f"   ⚠️  Error reading {task_filename}: {e}")
            
            # If no PR indices found, skip user
            if (not authored_pr_index and not reviewed_pr_index) or not start_date:
                print(f"   ❌ No valid PR indices found for {username}")
                total_failed += 1
                continue
            
            # Generate comment files
            try:
                success = generate_comments_for_user_combined(
                    username, pr_username, authored_pr_index, reviewed_pr_index,
                    pr_data_folder, comments_folder, start_date, end_date
                )
                
                if success:
                    total_generated += 1
                else:
                    total_failed += 1
            
            except Exception as e:
                print(f"   ❌ Error processing user: {e}")
                import traceback
                traceback.print_exc()
                total_failed += 1
        
        print("\n" + "=" * 80)
        print("✅ COMMENT FILE GENERATION COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"   Total users processed: {len(users)}")
        print(f"   Files generated/verified: {total_generated}")
        print(f"   Failed: {total_failed}")
        print(f"\n📁 Output folder: {comments_folder}")
    
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        import sys
        sys.exit(1)


if __name__ == "__main__":
    main()
