#!/usr/bin/env python3
"""
OKR Parser

Parses OKR CSV files from okrs/input directory and saves extracted/parsed
versions to okrs/parsed directory. Processes all users, skipping those that
have already been parsed.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict
from common import load_all_config


EXPECTED_HEADERS = ["Objectives", "Child Items", "Current", "Last month", "Target", "Status"]


def extract_okrs_from_csv(csv_path: Path) -> List[Dict]:
    """
    Read OKRs from CSV file with columns: Objective 1, Objective 2, Child Items
    Combine Objective 1 and Objective 2 into a single 'Objectives' column.
    
    Args:
        csv_path: Path to input CSV file
    
    Returns:
        List of OKR dictionaries
    """
    df = pd.read_csv(csv_path)
    print(f"      📄 CSV columns: {list(df.columns)}")
    
    rows = []
    for idx, row in df.iterrows():
        # Combine Objective 1 and Objective 2
        obj1 = str(row.get('Objective 1', '')).strip() if pd.notna(row.get('Objective 1')) else ''
        obj2 = str(row.get('Objective 2', '')).strip() if pd.notna(row.get('Objective 2')) else ''
        
        # Combine objectives: if both exist, join with " | ", otherwise use whichever exists
        if obj1 and obj2:
            objectives = f"{obj1} | {obj2}"
        elif obj1:
            objectives = obj1
        elif obj2:
            objectives = obj2
        else:
            objectives = ""
        
        # Get Child Items
        child_items = str(row.get('Child Items', '')).strip() if pd.notna(row.get('Child Items')) else ''
        
        # Only add if there's meaningful content
        if objectives or child_items:
            rec = {
                "slide": 1,  # Default slide number for CSV import
                "Objectives": objectives,
                "Child Items": child_items,
                "Current": "",
                "Last month": "",
                "Target": "",
                "Status": "",
            }
            rows.append(rec)
    
    return rows


def parse_okr_file(username: str, input_path: Path, output_dir: Path) -> bool:
    """
    Parse a single OKR CSV file and save extracted data.
    
    Args:
        username: Username
        input_path: Path to input CSV file
        output_dir: Output directory for parsed files
    
    Returns:
        True if parsing successful, False otherwise
    """
    try:
        # Define output file paths
        out_csv = output_dir / f"{username}_okrs_extracted.csv"
        out_json = output_dir / f"{username}_okrs_extracted.json"
        success_marker = output_dir / f"{username}_okrs_extracted._SUCCESS"
        
        # Read OKRs from CSV
        print(f"      📥 Reading OKRs from CSV: {input_path.name}")
        okrs = extract_okrs_from_csv(input_path)
        
        if not okrs:
            print(f"      ⚠️  No OKR data found in CSV")
            return False
        
        df = pd.DataFrame(okrs)
        
        # Stable column order
        col_order = ["slide"] + EXPECTED_HEADERS
        df = df[[c for c in col_order if c in df.columns]]
        
        # Forward fill empty Objective rows within each slide
        df["Objectives"] = df["Objectives"].replace("", pd.NA)
        df["Objectives"] = df.groupby("slide")["Objectives"].ffill().fillna("")
        
        # Save to CSV
        df.to_csv(out_csv, index=False)
        
        # Save to JSON with metadata
        json_data = {
            "user": username,
            "source_csv": str(input_path),
            "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
            "rows": df.to_dict(orient="records"),
        }
        
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2)
        
        # Write success marker
        success_marker.write_text("ok")
        
        print(f"      ✅ Extracted {len(df)} OKR rows")
        print(f"         CSV : {out_csv.name}")
        print(f"         JSON: {out_json.name}")
        
        return True
        
    except Exception as e:
        print(f"      ❌ Error parsing OKR file: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_already_parsed(username: str, output_dir: Path) -> bool:
    """
    Check if OKR file has already been parsed for this user.
    
    Args:
        username: Username
        output_dir: Output directory for parsed files
    
    Returns:
        True if already parsed, False otherwise
    """
    success_marker = output_dir / f"{username}_okrs_extracted._SUCCESS"
    return success_marker.exists()


def main():
    """Main execution function"""
    try:
        print("=" * 80)
        print("📋 OKR PARSER")
        print("=" * 80)
        print()
        
        # Load configuration
        print("🔄 Loading configuration...")
        all_config = load_all_config()
        
        config = all_config['config']
        users = all_config['users']
        paths = all_config['paths']
        
        base_dir = paths['base_dir']
        okr_folder = paths['okr_folder']
        
        # Define input and output directories
        input_dir = okr_folder / 'input'
        output_dir = okr_folder / 'parsed'
        
        print(f"✅ Configuration loaded")
        print(f"   Base dir: {base_dir}")
        print(f"   OKR folder: {okr_folder}")
        print(f"   Input dir: {input_dir}")
        print(f"   Output dir: {output_dir}")
        print(f"   Users: {len(users)}")
        
        # Ensure directories exist
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Iterate through users
        print("\n" + "=" * 80)
        print("🔄 PARSING OKR FILES")
        print("=" * 80)
        
        total_parsed = 0
        total_skipped = 0
        total_not_found = 0
        total_failed = 0
        
        for user in users:
            username = user['userName']
            first_name = user.get('firstName', '')
            last_name = user.get('lastName', '')
            full_name = f"{first_name} {last_name}".strip()
            
            print(f"\n👤 User: {full_name} ({username})")
            print("-" * 80)
            
            # Check if already parsed
            if check_already_parsed(username, output_dir):
                print(f"   ✅ Already parsed - skipping")
                total_skipped += 1
                continue
            
            # Look for input file: username_okrs.csv or username-okrs.csv
            input_file_underscore = input_dir / f"{username}_okrs.csv"
            input_file_dash = input_dir / f"{username}-okrs.csv"
            
            input_file = None
            if input_file_underscore.exists():
                input_file = input_file_underscore
            elif input_file_dash.exists():
                input_file = input_file_dash
            
            if not input_file:
                print(f"   ⚠️  Input file not found: {username}_okrs.csv or {username}-okrs.csv")
                total_not_found += 1
                continue
            
            print(f"   ✅ Found input file: {input_file.name}")
            
            # Parse the OKR file
            success = parse_okr_file(username, input_file, output_dir)
            
            if success:
                total_parsed += 1
            else:
                total_failed += 1
        
        print("\n" + "=" * 80)
        print("✅ OKR PARSING COMPLETE!")
        print("=" * 80)
        print(f"\n📊 Overall Summary:")
        print(f"   Total parsed: {total_parsed}")
        print(f"   Total skipped (already parsed): {total_skipped}")
        print(f"   Total not found: {total_not_found}")
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
