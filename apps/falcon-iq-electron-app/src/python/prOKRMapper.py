#!/usr/bin/env python3
"""
PR OKR Mapper

Maps OKRs to PRs that have been downloaded. Iterates through users and their
authored and reviewed PRs, checking for already-downloaded PR data and mapping
OKRs to them (skipping PRs that already have okrs.csv).
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from common import load_all_config


def check_pr_downloaded(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> bool:
    """
    Check if PR data has been downloaded.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        True if all 3 PR files exist, False otherwise
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    
    if not pr_dir.exists():
        return False
    
    # Check if all 3 files exist
    meta_file = pr_dir / f"pr_{pr_number}_meta.csv"
    comments_file = pr_dir / f"pr_{pr_number}_comments.csv"
    files_file = pr_dir / f"pr_{pr_number}_files.csv"
    
    return meta_file.exists() and comments_file.exists() and files_file.exists()


def check_okrs_exist(pr_data_folder: Path, owner: str, repo: str, pr_number: int, username: str, 
                     force_recalculate: bool = False) -> bool:
    """
    Check if okrs_{username}.csv already exists for this PR.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        username: Username for user-specific OKR file
        force_recalculate: If True, always return False to force recalculation
    
    Returns:
        True if okrs_{username}.csv exists and not forcing recalculation, False otherwise
    """
    if force_recalculate:
        return False
    
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    okrs_file = pr_dir / f"okrs_{username}.csv"
    
    return okrs_file.exists()


def load_okrs_for_user(username: str, okr_folder: Path) -> Optional[pd.DataFrame]:
    """
    Load parsed OKRs for a specific user.
    
    Args:
        username: Username
        okr_folder: OKR folder path
    
    Returns:
        DataFrame with OKR texts or None if not found
    """
    okr_parsed_dir = okr_folder / 'parsed'
    okr_file = okr_parsed_dir / f"{username}_okrs_extracted.csv"
    
    if not okr_file.exists():
        return None
    
    try:
        okrs_df = pd.read_csv(okr_file)
        
        # Keep only Objective + Child Item; forward-fill merged Objective rows
        okrs_df = okrs_df[["Objectives", "Child Items"]].fillna("")
        okrs_df["Objectives"] = okrs_df["Objectives"].astype(str).str.strip()
        okrs_df["Child Items"] = okrs_df["Child Items"].astype(str).str.strip()
        okrs_df["Objectives"] = okrs_df["Objectives"].replace("", pd.NA).ffill().fillna("")
        
        # Create combined OKR text
        okrs_df["okr_text"] = okrs_df["Objectives"] + " | " + okrs_df["Child Items"]
        
        return okrs_df
    except Exception as e:
        print(f"         ❌ Error loading OKRs: {e}")
        return None


def load_pr_text(pr_data_folder: Path, owner: str, repo: str, pr_number: int) -> str:
    """
    Load PR text from meta, comments, and files.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
    
    Returns:
        Combined PR text
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    
    pr_title = ""
    pr_body = ""
    comments_text = []
    filenames = []
    patches = []
    
    # Load meta
    meta_path = pr_dir / f"pr_{pr_number}_meta.csv"
    if meta_path.exists():
        try:
            meta_df = pd.read_csv(meta_path)
            if len(meta_df) > 0:
                pr_title = str(meta_df.iloc[0].get("pr_title", "") or "")
                pr_body = str(meta_df.iloc[0].get("pr_body", "") or "")
        except Exception:
            pass
    
    # Load comments
    comments_path = pr_dir / f"pr_{pr_number}_comments.csv"
    if comments_path.exists():
        try:
            comments_df = pd.read_csv(comments_path)
            if "body" in comments_df.columns:
                comments_text = comments_df["body"].dropna().astype(str).tolist()
        except Exception:
            pass
    
    # Load files
    files_path = pr_dir / f"pr_{pr_number}_files.csv"
    if files_path.exists():
        try:
            files_df = pd.read_csv(files_path)
            if "filename" in files_df.columns:
                filenames = files_df["filename"].dropna().astype(str).tolist()
            if "patch" in files_df.columns:
                # Truncate patches to avoid huge texts
                patches = [str(p)[:800] for p in files_df["patch"].dropna().astype(str).tolist()]
        except Exception:
            pass
    
    # Combine all text
    combined_text = "\n".join(
        [pr_title, pr_body] + comments_text + filenames + patches
    ).strip()
    
    return combined_text[:20000]  # Limit to 20k characters


def map_okr_simple(pr_text: str, okr_texts: list) -> tuple:
    """
    Simple string matching-based OKR mapping (fallback when OpenAI not available).
    Uses TF-IDF cosine similarity.
    
    Args:
        pr_text: PR text
        okr_texts: List of OKR texts
    
    Returns:
        Tuple of (best_okr_index, confidence_score)
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    
    if not okr_texts or not pr_text:
        return (-1, 0.0)
    
    try:
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(max_features=500, stop_words='english')
        vectors = vectorizer.fit_transform([pr_text] + okr_texts)
        
        # Calculate similarity
        pr_vector = vectors[0:1]
        okr_vectors = vectors[1:]
        similarities = cosine_similarity(pr_vector, okr_vectors)[0]
        
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]
        
        return (int(best_idx), float(best_score))
    except Exception as e:
        print(f"         ⚠️  Simple matching error: {e}")
        return (-1, 0.0)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text (rough approximation).
    ~4 characters per token for English text.
    """
    return len(text) // 4


def calculate_embedding_cost(tokens: int, model: str = "text-embedding-3-large") -> float:
    """
    Calculate OpenAI embedding cost.
    
    Pricing (as of 2024):
    - text-embedding-3-small: $0.02 / 1M tokens
    - text-embedding-3-large: $0.13 / 1M tokens
    """
    if "large" in model:
        cost_per_million = 0.13
    else:
        cost_per_million = 0.02
    
    return (tokens / 1_000_000) * cost_per_million


def map_okr_openai(pr_text: str, okr_texts: list, openai_api_key: str) -> tuple:
    """
    OpenAI embedding-based OKR mapping.
    
    Args:
        pr_text: PR text
        okr_texts: List of OKR texts
        openai_api_key: OpenAI API key
    
    Returns:
        Tuple of (best_okr_index, confidence_score, tokens_used, cost)
    """
    try:
        from openai import OpenAI
        import numpy as np
        
        client = OpenAI(api_key=openai_api_key)
        model = "text-embedding-3-large"
        
        # Estimate tokens
        pr_text_truncated = pr_text[:8000]
        pr_tokens = estimate_tokens(pr_text_truncated)
        okr_tokens = sum(estimate_tokens(okr) for okr in okr_texts)
        total_tokens = pr_tokens + okr_tokens
        
        # Get embeddings
        pr_response = client.embeddings.create(input=[pr_text_truncated], model=model)
        pr_embedding = np.array(pr_response.data[0].embedding)
        
        # Batch embed OKRs (only once per user, cached in memory)
        okr_response = client.embeddings.create(input=okr_texts, model=model)
        okr_embeddings = np.array([data.embedding for data in okr_response.data])
        
        # Calculate cosine similarity
        pr_norm = pr_embedding / np.linalg.norm(pr_embedding)
        okr_norms = okr_embeddings / np.linalg.norm(okr_embeddings, axis=1, keepdims=True)
        similarities = np.dot(okr_norms, pr_norm)
        
        best_idx = similarities.argmax()
        best_score = similarities[best_idx]
        
        # Calculate cost
        cost = calculate_embedding_cost(total_tokens, model)
        
        return (int(best_idx), float(best_score), total_tokens, cost)
    except Exception as e:
        print(f"         ⚠️  OpenAI mapping error: {e}")
        return (-1, 0.0, 0, 0.0)


def map_okrs_for_pr(pr_data_folder: Path, owner: str, repo: str, pr_number: int, username: str, 
                    okr_folder: Path, openai_api_key: Optional[str] = None) -> Dict:
    """
    Map OKRs for a specific PR and user using intelligent matching.
    
    Args:
        pr_data_folder: Base PR data folder path
        owner: Repository owner
        repo: Repository name
        pr_number: PR number
        username: Username for user-specific OKR file
        okr_folder: OKR folder path
        openai_api_key: Optional OpenAI API key for advanced matching
    
    Returns:
        Dictionary with success status, tokens, and cost
    """
    pr_dir = pr_data_folder / owner / repo / f"pr_{pr_number}"
    okrs_file = pr_dir / f"okrs_{username}.csv"
    
    result = {
        "success": False,
        "tokens": 0,
        "cost": 0.0
    }
    
    try:
        # Load user's OKRs
        okrs_df = load_okrs_for_user(username, okr_folder)
        if okrs_df is None or len(okrs_df) == 0:
            print(f"         ⚠️  No OKRs found for user {username}")
            return result
        
        okr_texts = okrs_df["okr_text"].tolist()
        
        # Load PR text
        pr_text = load_pr_text(pr_data_folder, owner, repo, pr_number)
        if not pr_text or len(pr_text) < 10:
            print(f"         ⚠️  No meaningful PR text found")
            return result
        
        # Map OKR using best available method
        if openai_api_key:
            best_idx, confidence, tokens, cost = map_okr_openai(pr_text, okr_texts, openai_api_key)
            result["tokens"] = tokens
            result["cost"] = cost
        else:
            best_idx, confidence = map_okr_simple(pr_text, okr_texts)
        
        if best_idx < 0:
            print(f"         ⚠️  OKR matching failed")
            return result
        
        # Create output with matched OKR
        matched_okr = okrs_df.iloc[best_idx]
        okr_result = {
            "okr_objective": [matched_okr["Objectives"]],
            "okr_child_item": [matched_okr["Child Items"]],
            "okr_text": [matched_okr["okr_text"]],
            "confidence": [confidence],
            "method": ["openai" if openai_api_key else "tfidf"]
        }
        
        result_df = pd.DataFrame(okr_result)
        result_df.to_csv(okrs_file, index=False)
        
        result["success"] = True
        return result
    except Exception as e:
        print(f"         ❌ Failed to map OKRs: {e}")
        import traceback
        traceback.print_exc()
        return result


def load_status(status_filepath: Path) -> Dict:
    """
    Load status from status file, or create new status if file doesn't exist.
    
    Args:
        status_filepath: Path to status file
    
    Returns:
        Status dictionary
    """
    if status_filepath.exists():
        with open(status_filepath, 'r') as f:
            return json.load(f)
    else:
        return {
            "status": "not_started",
            "current_row": 0,
            "mapped_count": 0,
            "skipped_count": 0
        }


def save_status(status_filepath: Path, status_data: Dict):
    """
    Save status to status file.
    
    Args:
        status_filepath: Path to status file
        status_data: Status dictionary
    """
    with open(status_filepath, 'w') as f:
        json.dump(status_data, f, indent=2)


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("🗺️  PR OKR MAPPER")
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
        okr_folder = paths['okr_folder']
        
        # Get settings
        openai_api_key = settings.get('openai_api_key')
        force_recalculate = settings.get('force_recalculate_okrs', False)
        
        if force_recalculate:
            print("⚠️  Force recalculate mode: Will overwrite existing OKR files")
            print()
        
        print(f"✅ Configuration loaded")
        print(f"   Task folder: {task_folder}")
        print(f"   PR data folder: {pr_data_folder}")
        print(f"   Search folder: {search_folder}")
        print(f"   OKR folder: {okr_folder}")
        print(f"   Users: {len(users)}")
        print(f"   OpenAI API key: {'✅ Available' if openai_api_key else '❌ Not available (using TF-IDF)'}")
        print(f"   Force recalculate: {'✅ Enabled' if force_recalculate else '❌ Disabled'}")
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("🔄 MAPPING OKRs TO PRs")
        print("=" * 80)
        
        task_types = ["authored", "reviewer"]
        total_mapped = 0
        total_skipped = 0
        total_tokens = 0
        total_cost = 0.0
        MAPPING_LIMIT_PER_USER = 10  # Map 10 OKRs per user (excluding skipped)
        
        for user in users:
            username = user['userName']
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            print(f"\n👤 User: {full_name} ({username})")
            print("-" * 80)
            
            # Track mapped count per user
            user_mapped = 0
            
            for task_type in task_types:
                if user_mapped >= MAPPING_LIMIT_PER_USER:
                    print(f"\n   ✅ Reached mapping limit of {MAPPING_LIMIT_PER_USER} OKRs for {username} - moving to next user")
                    break
                
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                # Status file for OKR mapping
                okr_status_filename = f"pr_{task_type}_okr_{username}_status.json"
                okr_status_filepath = task_folder / okr_status_filename
                
                print(f"\n   📋 Task Type: {task_type}")
                
                # Check if task file exists
                if not task_filepath.exists():
                    print(f"      ⚠️  Task file not found: {task_filename}")
                    continue
                
                # Read task file
                with open(task_filepath, 'r') as f:
                    task_data = json.load(f)
                
                print(f"      ✅ Task file: {task_filename}")
                
                # Check if CSV data file exists
                start_date = task_data.get('start_date')
                end_date = task_data.get('end_date')
                csv_filename = f"pr_{task_type}_{username}_{start_date}_{end_date}.csv"
                csv_filepath = search_folder / csv_filename
                
                if not csv_filepath.exists():
                    print(f"      ❌ CSV data file NOT found: {csv_filename}")
                    continue
                
                print(f"      ✅ CSV data file exists: {csv_filename}")
                
                # Load OKR mapping status
                okr_status = load_status(okr_status_filepath)
                current_row = okr_status.get('current_row', 0)
                mapped_count = okr_status.get('mapped_count', 0)
                skipped_count = okr_status.get('skipped_count', 0)
                
                # Check if OKR mapping is complete (always honor completed status)
                if okr_status.get('status') == 'completed':
                    print(f"      ✅ OKR mapping already completed - skipping")
                    total_mapped += mapped_count
                    total_skipped += skipped_count
                    continue
                
                # Read CSV file
                try:
                    df = pd.read_csv(csv_filepath)
                    total_prs = len(df)
                    print(f"      📄 Found {total_prs} PRs in CSV")
                    
                    if total_prs == 0:
                        print(f"      ℹ️  No PRs to map")
                        okr_status['status'] = 'completed'
                        save_status(okr_status_filepath, okr_status)
                        continue
                    
                    # Check if already completed
                    if current_row >= total_prs:
                        print(f"      ✅ All PRs already processed ({current_row}/{total_prs})")
                        okr_status['status'] = 'completed'
                        save_status(okr_status_filepath, okr_status)
                        total_mapped += mapped_count
                        total_skipped += skipped_count
                        continue
                    
                    print(f"      📍 Starting from row: {current_row}")
                    print(f"      📊 Previous: {mapped_count} mapped, {skipped_count} skipped")
                    
                    # Set status to in_progress
                    okr_status['status'] = 'in_progress'
                    save_status(okr_status_filepath, okr_status)
                    
                    # Process PRs starting from current_row
                    batch_mapped = 0
                    batch_skipped = 0
                    
                    print(f"      🔄 Mapping OKRs (starting from row {current_row + 1})...")
                    
                    for idx in range(current_row, total_prs):
                        # Stop if we've reached the per-user mapping limit
                        if user_mapped >= MAPPING_LIMIT_PER_USER:
                            print(f"      🛑 Reached mapping limit of {MAPPING_LIMIT_PER_USER} OKRs for this user")
                            break
                        
                        row = df.iloc[idx]
                        owner = row.get('owner')
                        repo = row.get('repo')
                        pr_number = int(row.get('pr_number'))
                        
                        # Check if PR data is downloaded
                        if not check_pr_downloaded(pr_data_folder, owner, repo, pr_number):
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [NOT DOWNLOADED - SKIPPED]")
                            
                            # Update status
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            save_status(okr_status_filepath, okr_status)
                            continue
                        
                        # Check if okrs_{username}.csv already exists
                        if check_okrs_exist(pr_data_folder, owner, repo, pr_number, username, force_recalculate):
                            batch_skipped += 1
                            total_skipped += 1
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [ALREADY HAS OKRs FOR {username} - SKIPPED]")
                            
                            # Update status
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            okr_status['skipped_count'] = skipped_count + batch_skipped
                            save_status(okr_status_filepath, okr_status)
                            continue
                        
                        # Map OKRs for this PR and user
                        try:
                            mapping_result = map_okrs_for_pr(pr_data_folder, owner, repo, pr_number, username, 
                                                            okr_folder, openai_api_key)
                            
                            if mapping_result["success"]:
                                batch_mapped += 1
                                total_mapped += 1
                                user_mapped += 1
                                
                                # Track costs
                                pr_tokens = mapping_result.get("tokens", 0)
                                pr_cost = mapping_result.get("cost", 0.0)
                                total_tokens += pr_tokens
                                total_cost += pr_cost
                                
                                # Print mapping result with cost info
                                if openai_api_key and pr_cost > 0:
                                    print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [OKRs MAPPED FOR {username}]")
                                    print(f"            💰 Tokens: {pr_tokens:,} | Cost: ${pr_cost:.6f} | Cumulative: ${total_cost:.6f}")
                                else:
                                    print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [OKRs MAPPED FOR {username}]")
                            else:
                                print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [MAPPING FAILED FOR {username}]")
                            
                            # Update status after each PR
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            okr_status['mapped_count'] = mapped_count + batch_mapped
                            okr_status['skipped_count'] = skipped_count + batch_skipped
                            save_status(okr_status_filepath, okr_status)
                        
                        except Exception as e:
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [ERROR: {str(e)}]")
                            
                            # Update current_row even on error
                            current_row = idx + 1
                            okr_status['current_row'] = current_row
                            save_status(okr_status_filepath, okr_status)
                    
                    print(f"      📊 Batch Summary: {batch_mapped} mapped, {batch_skipped} skipped")
                    print(f"      📍 Progress: {current_row}/{total_prs} PRs processed")
                    
                    # Check if all PRs are processed
                    if current_row >= total_prs:
                        okr_status['status'] = 'completed'
                        okr_status['current_row'] = total_prs
                        save_status(okr_status_filepath, okr_status)
                        print(f"      ✅ All PRs processed! Updated status to: completed")
                    else:
                        print(f"      ⏸️  Stopped. Run again to continue from row {current_row + 1}")
                
                except Exception as e:
                    print(f"      ❌ Error processing CSV: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Print per-user summary
            if user_mapped > 0 or total_skipped > 0:
                print(f"\n   📊 Summary for {username}: {user_mapped} OKRs mapped")
        
        print("\n" + "=" * 80)
        print("✅ OKR MAPPING COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Overall Summary:")
        print(f"   Total mapped: {total_mapped}")
        print(f"   Total skipped: {total_skipped}")
        
        if openai_api_key and total_cost > 0:
            print(f"\n💰 OpenAI API Usage:")
            print(f"   Total tokens: {total_tokens:,}")
            print(f"   Total cost: ${total_cost:.6f}")
            print(f"   Average cost per PR: ${total_cost/total_mapped:.6f}" if total_mapped > 0 else "")
        
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
