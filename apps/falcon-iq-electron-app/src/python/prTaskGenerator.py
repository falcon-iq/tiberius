#!/usr/bin/env python3
"""
PR Task Generator

Generates PR tasks for downloading authored PRs and review comments for all users.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from common import load_all_config


def generate_pr_task(
    username: str,
    pr_user_name: str,
    task_type: str,
    start_date: str,
    end_date: str,
    base_dir: Path,
    org: str,
    existing_min_start_date: Optional[str] = None
) -> Dict:
    """
    Generate a PR task dictionary.
    
    Args:
        username: User's username (e.g., "jbaik")
        pr_user_name: GitHub username (e.g., "jbaik_LinkedIn")
        task_type: "authored" or "reviewer"
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        base_dir: Base directory path
        org: GitHub organization
        existing_min_start_date: Min start date from existing task (if any)
    
    Returns:
        Dictionary with PR task data
    """
    # Calculate min_start_date
    if existing_min_start_date is None:
        # No older task exists, use start_date as min_start_date
        min_start_date = start_date
    else:
        # Older task exists, use minimum of existing_min_start_date and new start_date
        min_start_date = min(existing_min_start_date, start_date)
    
    # Create task dictionary with snake_case field names
    task = {
        "username": username,
        "start_date": start_date,
        "end_date": end_date,
        "min_start_date": min_start_date,
        "total_rows": 0
    }
    
    return task


def main():
    """Main execution"""
    print("=" * 80)
    print("📋 PR TASK GENERATOR")
    print("=" * 80)
    print()
    
    try:
        # Load all configuration using common module
        print("🔄 Loading configuration...")
        all_config = load_all_config()
        
        config = all_config['config']
        settings = all_config['settings']
        users = all_config['users']
        paths = all_config['paths']
        
        base_dir = paths['base_dir']
        task_folder = paths['task_folder']
        org = settings.get('org', 'linkedin-multiproduct')
        
        # Get global start_date from user-settings.json (in YYYY-MM-DD format)
        global_start_date = settings.get('start_date')
        if not global_start_date:
            raise ValueError("start_date not found in user-settings.json")
        
        # Today's date in YYYY-MM-DD format
        today = datetime.now().strftime("%Y-%m-%d")
        
        print(f"✅ Configuration loaded")
        print(f"   Base dir: {base_dir}")
        print(f"   Organization: {org}")
        print(f"   Task folder: {task_folder}")
        print(f"   Global start date: {global_start_date}")
        print(f"   End date (today): {today}")
        print(f"   Users: {len(users)}")
        
        # Ensure task folder exists
        task_folder.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 80)
        print("🔄 GENERATING PR TASKS")
        print("=" * 80)
        
        new_tasks = []
        
        # Iterate through all users
        for user in users:
            username = user.get('userName')
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            pr_user_name = user.get('prUserName')
            
            if not username or not pr_user_name:
                print(f"⚠️  Skipping user with missing userName or prUserName: {user}")
                continue
            
            print(f"\n👤 User: {first_name} {last_name} ({username})")
            print("-" * 80)
            
            # Check for both task types
            for task_type in ["authored", "reviewer"]:
                # Task file format: pr_{type}_{username}.json
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                print(f"\n   📋 Task Type: {task_type}")
                print(f"      Looking for: {task_filename}")
                
                if task_filepath.exists():
                    print(f"      ✅ Task file EXISTS")
                    
                    # Check status file
                    status_filename = f"pr_{task_type}_{username}_status.json"
                    status_filepath = task_folder / status_filename
                    
                    if status_filepath.exists():
                        try:
                            with open(status_filepath, 'r') as f:
                                status_data = json.load(f)
                            
                            task_status = status_data.get('status')
                            print(f"      📊 Status file exists: {status_filename}")
                            print(f"         Status: {task_status}")
                            
                            # If status is not "completed", skip this task
                            if task_status != "completed":
                                print(f"      ⏭️  Skipping - status is not 'completed' (current: {task_status})")
                                continue
                            else:
                                print(f"      ✅ Status is 'completed' - can generate new task")
                                # Delete status file immediately since task is completed
                                status_filepath.unlink()
                                print(f"      🗑️  Deleted status file: {status_filename}")
                        
                        except Exception as e:
                            print(f"      ⚠️  Warning: Could not read status file: {e}")
                            print(f"      Proceeding with task generation...")
                    else:
                        print(f"      ℹ️  No status file found - creating one")
                        # Create status file with not_started status
                        status_data = {
                            "status": "not_started",
                            "current_row": 0
                        }
                        
                        with open(status_filepath, 'w') as f:
                            json.dump(status_data, f, indent=2)
                        
                        print(f"      ✅ Created status file: {status_filename}")
                        print(f"      ⏭️  Skipping - status is 'not_started'")
                        continue
                    
                    # Load existing task
                    try:
                        with open(task_filepath, 'r') as f:
                            existing_task = json.load(f)
                        
                        print(f"      📄 Existing task:")
                        print(f"         Start Date: {existing_task.get('start_date')}")
                        print(f"         End Date: {existing_task.get('end_date')}")
                        print(f"         Min Start Date: {existing_task.get('min_start_date')}")
                        print(f"         Total Rows: {existing_task.get('total_rows', 0)}")
                        
                        # Determine new task dates based on existing task
                        existing_start_date = existing_task.get('start_date')
                        existing_end_date = existing_task.get('end_date')
                        existing_min_start_date = existing_task.get('min_start_date', existing_start_date)
                        
                        # Check if we need to backfill (global start_date < existing min_start_date)
                        # Using string comparison works for YYYY-MM-DD format
                        if global_start_date < existing_min_start_date:
                            # Backfill scenario
                            new_start_date = global_start_date
                            new_end_date = today
                            print(f"      🔙 Backfill needed: global start_date ({global_start_date}) < existing min_start_date ({existing_min_start_date})")
                            
                            # Check if task is already up to date (covers this range)
                            if new_start_date == existing_start_date and new_end_date == existing_end_date:
                                print(f"      ✅ No new task needed (already covers this range)")
                                # Recreate status file since we deleted it earlier
                                status_data = {
                                    "status": "completed",
                                    "current_row": 0
                                }
                                with open(status_filepath, 'w') as f:
                                    json.dump(status_data, f, indent=2)
                                print(f"      ✅ Recreated status file: {status_filename} (status: completed)")
                                continue
                        else:
                            # Incremental scenario: start from old end_date + 1 day
                            old_end_dt = datetime.strptime(existing_end_date, "%Y-%m-%d")
                            new_start_dt = old_end_dt
                            new_start_date = new_start_dt.strftime("%Y-%m-%d")
                            new_end_date = today
                            
                            # Check if new task is needed
                            if new_start_date > today:
                                print(f"      ✅ No new task needed (already up to date)")
                                # Recreate status file since we deleted it earlier
                                status_data = {
                                    "status": "completed",
                                    "current_row": 0
                                }
                                with open(status_filepath, 'w') as f:
                                    json.dump(status_data, f, indent=2)
                                print(f"      ✅ Recreated status file: {status_filename} (status: completed)")
                                continue
                            
                            print(f"      ➕ Incremental update: new task from {new_start_date} to {new_end_date}")
                        
                        # Generate new task
                        print(f"      ✨ Generating task: {new_start_date} to {new_end_date}")
                        new_task = generate_pr_task(
                            username=username,
                            pr_user_name=pr_user_name,
                            task_type=task_type,
                            start_date=new_start_date,
                            end_date=new_end_date,
                            base_dir=base_dir,
                            org=org,
                            existing_min_start_date=existing_min_start_date  # Pass existing min_start_date
                        )
                        
                        new_tasks.append((new_task, task_type))
                        print(f"      ✅ Task generated with min_start_date: {new_task['min_start_date']}")
                        
                    except Exception as e:
                        print(f"      ❌ Error reading/processing existing task: {e}")
                        
                else:
                    print(f"      ❌ Task file DOES NOT EXIST")
                    
                    # Generate new task from global start_date to today
                    new_start_date = global_start_date
                    new_end_date = today
                    
                    print(f"      ✨ Generating new task: {new_start_date} to {new_end_date}")
                    
                    new_task = generate_pr_task(
                        username=username,
                        pr_user_name=pr_user_name,
                        task_type=task_type,
                        start_date=new_start_date,
                        end_date=new_end_date,
                        base_dir=base_dir,
                        org=org,
                        existing_min_start_date=None  # No existing task, so min_start_date = start_date
                    )
                    
                    new_tasks.append((new_task, task_type))
                    print(f"      ✅ Task generated with min_start_date: {new_task['min_start_date']}")
        
        # Save all generated tasks
        if new_tasks:
            print("\n" + "=" * 80)
            print("💾 SAVING TASKS")
            print("=" * 80)
            
            for task, task_type in new_tasks:
                username = task['username']
                
                # Save as pr_{type}_{username}.json
                task_filename = f"pr_{task_type}_{username}.json"
                task_filepath = task_folder / task_filename
                
                with open(task_filepath, 'w') as f:
                    json.dump(task, f, indent=2)
                
                print(f"✅ Saved: {task_filename}")
                
                # Create corresponding status file
                status_filename = f"pr_{task_type}_{username}_status.json"
                status_filepath = task_folder / status_filename
                
                status_data = {
                    "status": "not_started",
                    "current_row": 0
                }
                
                with open(status_filepath, 'w') as f:
                    json.dump(status_data, f, indent=2)
                
                print(f"✅ Created status file: {status_filename}")
            
            print(f"\n✅ Saved {len(new_tasks)} task(s) to {task_folder}")
        else:
            print("\n✅ No new tasks to generate - all users are up to date!")
        
        print("\n" + "=" * 80)
        print("✅ TASK GENERATION COMPLETE!")
        print("=" * 80)
        
        if new_tasks:
            print(f"\n📊 Summary:")
            print(f"   Total new tasks: {len(new_tasks)}")
            
            # Group by type
            authored_count = sum(1 for task, ttype in new_tasks if ttype == "authored")
            reviewer_count = sum(1 for task, ttype in new_tasks if ttype == "reviewer")
            
            print(f"   Authored tasks: {authored_count}")
            print(f"   Reviewer tasks: {reviewer_count}")
        
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
