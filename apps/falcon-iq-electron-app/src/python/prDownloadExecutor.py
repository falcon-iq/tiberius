#!/usr/bin/env python3
"""
PR Download Executor
Downloads full PR details (metadata, comments, files) for PRs listed in search CSV files
"""

import json
import pandas as pd
from pathlib import Path
from common import load_all_config
from githubCommonFunctions import extract_pr_full


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("📥 PR DOWNLOAD EXECUTOR")
        print("=" * 80)
        
        # Load configuration
        print("\n🔄 Loading configuration...")
        all_config = load_all_config()
        
        config = all_config['config']
        settings = all_config['settings']
        users = all_config['users']
        paths = all_config['paths']
        
        task_folder = paths['task_folder']
        pr_data_folder = paths['pr_data_folder']
        search_folder = pr_data_folder / 'search'
        
        # Get GitHub settings
        org = settings.get('org')
        github_token = settings.get('github_token')
        
        if not github_token:
            print("❌ Error: No GitHub token found in settings. Cannot download PRs.")
            return
        
        print(f"✅ Configuration loaded")
        print(f"   Task folder: {task_folder}")
        print(f"   PR data folder: {pr_data_folder}")
        print(f"   Search folder: {search_folder}")
        print(f"   Organization: {org}")
        print(f"   Users: {len(users)}")
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("📥 DOWNLOADING PR DETAILS")
        print("=" * 80)
        
        task_types = ["authored", "reviewer"]
        total_downloaded = 0
        total_skipped = 0
        total_failed = 0
        
        for user in users:
            username = user['userName']
            pr_username = user.get('prUserName', username)
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            print(f"\n👤 User: {full_name} ({username})")
            print(f"   GitHub Username: {pr_username}")
            print("-" * 80)
            
            for task_type in task_types:
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                status_filename = f"pr_{task_type}_{username}_status.json"
                status_filepath = task_folder / status_filename
                
                print(f"\n   📋 Task Type: {task_type}")
                
                # Check if task file exists
                if not task_filepath.exists():
                    print(f"      ⚠️  Task file not found: {task_filename}")
                    continue
                
                # Read task file
                with open(task_filepath, 'r') as f:
                    task_data = json.load(f)
                
                print(f"      ✅ Task file: {task_filename}")
                print(f"         Start Date: {task_data.get('start_date')}")
                print(f"         End Date: {task_data.get('end_date')}")
                print(f"         Total Rows: {task_data.get('total_rows', 0)}")
                
                # Check if CSV data file exists
                start_date = task_data.get('start_date')
                end_date = task_data.get('end_date')
                csv_filename = f"pr_{task_type}_{username}_{start_date}_{end_date}.csv"
                csv_filepath = search_folder / csv_filename
                
                if not csv_filepath.exists():
                    print(f"      ❌ CSV data file NOT found: {csv_filename}")
                    print(f"         Run prSearchTaskExecutor.py first to generate CSV files")
                    continue
                
                print(f"      ✅ CSV data file exists: {csv_filename}")
                
                # Check status - only proceed if status is pr-search-file-downloaded
                if status_filepath.exists():
                    with open(status_filepath, 'r') as f:
                        status_data = json.load(f)
                    
                    current_status = status_data.get('status')
                    print(f"      📊 Current status: {current_status}")
                    
                    if current_status == 'pr-details-downloaded':
                        print(f"      ✅ PR details already downloaded - skipping")
                        continue
                    elif current_status != 'pr-search-file-downloaded':
                        print(f"      ⏭️  Skipping - status is not 'pr-search-file-downloaded'")
                        continue
                else:
                    print(f"      ⚠️  No status file found - creating one")
                    status_data = {
                        "status": "not_started",
                        "current_row": 0
                    }
                    with open(status_filepath, 'w') as f:
                        json.dump(status_data, f, indent=2)
                    print(f"      ⏭️  Skipping - status is 'not_started'")
                    continue
                
                # Read CSV file and download PR details
                try:
                    df = pd.read_csv(csv_filepath)
                    total_prs = len(df)
                    print(f"      📄 Found {total_prs} PRs in CSV")
                    
                    if total_prs == 0:
                        print(f"      ℹ️  No PRs to download")
                        # Update status to pr-details-downloaded even if no PRs
                        status_data['status'] = 'pr-details-downloaded'
                        status_data['current_row'] = 0
                        with open(status_filepath, 'w') as f:
                            json.dump(status_data, f, indent=2)
                        print(f"      ✅ Updated status to: pr-details-downloaded")
                        continue
                    
                    # Get current row from status
                    current_row = status_data.get('current_row', 0)
                    print(f"      📍 Starting from row: {current_row}")
                    
                    # Check if already completed
                    if current_row >= total_prs:
                        print(f"      ✅ All PRs already downloaded ({current_row}/{total_prs})")
                        status_data['status'] = 'pr-details-downloaded'
                        status_data['current_row'] = total_prs
                        with open(status_filepath, 'w') as f:
                            json.dump(status_data, f, indent=2)
                        continue
                    
                    # Process only next 10 PRs
                    BATCH_SIZE = 10
                    end_row = min(current_row + BATCH_SIZE, total_prs)
                    prs_to_process = df.iloc[current_row:end_row]
                    
                    downloaded_count = 0
                    skipped_count = 0
                    failed_count = 0
                    
                    print(f"      🔄 Downloading PR details (rows {current_row + 1} to {end_row} of {total_prs})...")
                    
                    for idx, row in prs_to_process.iterrows():
                        owner = row.get('owner')
                        repo = row.get('repo')
                        pr_number = int(row.get('pr_number'))
                        
                        try:
                            result = extract_pr_full(
                                owner=owner,
                                repo=repo,
                                pr_number=pr_number,
                                token=github_token,
                                base_output_dir=pr_data_folder
                            )
                            
                            if result == "skipped":
                                skipped_count += 1
                                total_skipped += 1
                                print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [SKIPPED]")
                            else:
                                downloaded_count += 1
                                total_downloaded += 1
                                print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [DOWNLOADED]")
                            
                            # Update current_row after each PR
                            current_row = idx + 1
                            status_data['current_row'] = current_row
                            with open(status_filepath, 'w') as f:
                                json.dump(status_data, f, indent=2)
                        
                        except Exception as e:
                            failed_count += 1
                            total_failed += 1
                            print(f"         ({idx + 1}/{total_prs}) {owner}/{repo} #{pr_number} [FAILED: {str(e)}]")
                            
                            # Update current_row even on failure
                            current_row = idx + 1
                            status_data['current_row'] = current_row
                            with open(status_filepath, 'w') as f:
                                json.dump(status_data, f, indent=2)
                    
                    print(f"      📊 Batch Summary: {downloaded_count} downloaded, {skipped_count} skipped, {failed_count} failed")
                    print(f"      📍 Progress: {current_row}/{total_prs} PRs processed")
                    
                    # Check if all PRs are downloaded
                    if current_row >= total_prs:
                        status_data['status'] = 'pr-details-downloaded'
                        status_data['current_row'] = total_prs
                        with open(status_filepath, 'w') as f:
                            json.dump(status_data, f, indent=2)
                        print(f"      ✅ All PRs downloaded! Updated status to: pr-details-downloaded")
                    else:
                        print(f"      ⏸️  Batch complete. Run again to continue from row {current_row + 1}")
                
                except Exception as e:
                    print(f"      ❌ Error processing CSV: {e}")
                    import traceback
                    traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("✅ PR DOWNLOAD COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Overall Summary:")
        print(f"   Total downloaded: {total_downloaded}")
        print(f"   Total skipped: {total_skipped}")
        print(f"   Total failed: {total_failed}")
        
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
