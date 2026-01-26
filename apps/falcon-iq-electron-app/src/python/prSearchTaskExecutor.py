#!/usr/bin/env python3
"""
PR Search Task Executor
Reads and processes PR tasks for all users
"""

import json
from pathlib import Path
from common import load_all_config
from githubCommonFunctions import search_and_save_prs


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("📋 PR SEARCH TASK EXECUTOR")
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
            print("⚠️  Warning: No GitHub token found in settings. Cannot download PRs from GitHub.")
        
        print(f"✅ Configuration loaded")
        print(f"   Task folder: {task_folder}")
        print(f"   PR data folder: {pr_data_folder}")
        print(f"   Search folder: {search_folder}")
        print(f"   Organization: {org}")
        print(f"   Users: {len(users)}")
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("📋 PROCESSING TASKS")
        print("=" * 80)
        
        task_types = ["authored", "reviewer"]
        
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
                if task_filepath.exists():
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
                    
                    if csv_filepath.exists():
                        print(f"      ✅ CSV data file exists: {csv_filename}")
                        
                        # Update status to pr-search-file-downloaded
                        if status_filepath.exists():
                            with open(status_filepath, 'r') as f:
                                status_data = json.load(f)
                            
                            # Update status if not already set
                            if status_data.get('status') != 'pr-search-file-downloaded':
                                status_data['status'] = 'pr-search-file-downloaded'
                                with open(status_filepath, 'w') as f:
                                    json.dump(status_data, f, indent=2)
                                print(f"      ✅ Updated status to: pr-search-file-downloaded")
                    else:
                        print(f"      ❌ CSV data file NOT found: {csv_filename}")
                        
                        # Try to download from GitHub if token is available
                        if github_token and org:
                            try:
                                num_prs = search_and_save_prs(
                                    task_type=task_type,
                                    username=username,
                                    pr_username=pr_username,
                                    org=org,
                                    start_date=start_date,
                                    end_date=end_date,
                                    token=github_token,
                                    output_csv_path=csv_filepath
                                )
                                
                                # Update total_rows in task file
                                task_data['total_rows'] = num_prs
                                with open(task_filepath, 'w') as f:
                                    json.dump(task_data, f, indent=2)
                                print(f"      ✅ Updated task file with total_rows: {num_prs}")
                                
                                # Update status to pr-search-file-downloaded
                                if status_filepath.exists():
                                    with open(status_filepath, 'r') as f:
                                        status_data = json.load(f)
                                    
                                    status_data['status'] = 'pr-search-file-downloaded'
                                    with open(status_filepath, 'w') as f:
                                        json.dump(status_data, f, indent=2)
                                    print(f"      ✅ Updated status to: pr-search-file-downloaded")
                                
                            except Exception as e:
                                print(f"      ❌ Failed to download from GitHub: {e}")
                        else:
                            print(f"      ⚠️  Cannot download - missing GitHub token or org")
                    
                    # Check if status file exists
                    if status_filepath.exists():
                        with open(status_filepath, 'r') as f:
                            status_data = json.load(f)
                        
                        print(f"      📊 Status file: {status_filename}")
                        print(f"         Status: {status_data.get('status')}")
                        print(f"         Current Row: {status_data.get('current_row', 0)}")
                        if 'total_rows' in status_data:
                            print(f"         Total Rows: {status_data.get('total_rows')}")
                    else:
                        print(f"      ⚠️  No status file found - creating one")
                        # Create status file with not_started status
                        status_data = {
                            "status": "not_started",
                            "current_row": 0
                        }
                        
                        with open(status_filepath, 'w') as f:
                            json.dump(status_data, f, indent=2)
                        
                        print(f"      ✅ Created status file: {status_filename}")
                        print(f"         Status: not_started")
                        print(f"         Current Row: 0")
                else:
                    print(f"      ❌ Task file not found: {task_filename}")
        
        print("\n" + "=" * 80)
        print("✅ TASK PROCESSING COMPLETE!")
        print("=" * 80)
        
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
