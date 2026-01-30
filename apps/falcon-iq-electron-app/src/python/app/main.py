#!/usr/bin/env python3
"""Main CLI entry point for PR Analytics Agent."""

import argparse
import sys
import os
import re
from typing import Optional
from pathlib import Path


def format_table(rows: list, max_rows: int = 20) -> str:
    """
    Format query results as a markdown table.
    
    Args:
        rows: List of dictionaries (query results)
        max_rows: Maximum rows to display
    
    Returns:
        Formatted markdown table
    """
    if not rows:
        return "_No results found_"
    
    # Get column names
    columns = list(rows[0].keys())
    
    # Build table
    lines = []
    
    # Header
    header = "| " + " | ".join(str(col) for col in columns) + " |"
    separator = "|" + "|".join("-" * (len(str(col)) + 2) for col in columns) + "|"
    
    lines.append(header)
    lines.append(separator)
    
    # Rows (limit display)
    for i, row in enumerate(rows[:max_rows]):
        values = [str(row.get(col, "")) for col in columns]
        row_line = "| " + " | ".join(values) + " |"
        lines.append(row_line)
    
    if len(rows) > max_rows:
        lines.append("")
        lines.append(f"_({len(rows) - max_rows} more rows not shown)_")
    
    return "\n".join(lines)


def print_summary(state: dict, show_sql: bool = True):
    """
    Print agent results in a nice format.
    
    Args:
        state: Final agent state
        show_sql: Whether to show SQL query
    """
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    if show_sql and state.get("sql"):
        print("SQL Query:")
        print("```sql")
        print(state["sql"])
        print("```")
        print()
    
    if state.get("results"):
        print(f"Data ({len(state['results'])} rows):")
        print()
        print(format_table(state["results"]))
        print()
    
    if state.get("summary"):
        print("Summary:")
        print(state["summary"])
    else:
        print("❌ No summary available")
    
    print()
    print("=" * 80)


def handle_special_tools(question: str, username: str) -> Optional[str]:
    """
    Handle special tool commands that don't use SQL queries.
    Returns formatted output if a special tool was used, None otherwise.
    """
    from app.config import SQLITE_PATH, get_api_key
    from app.tools_sqlite import get_db_connection
    from app.tools_extended import (
        get_pr_body_tool,
        get_comment_body_tool,
        get_pr_files_tool,
        generate_okr_update_tool,
        format_pr_body_response,
        format_comment_response,
        format_files_response,
        format_okr_update_response
    )
    
    question_lower = question.lower()
    
    # Pattern 1: Show PR body - "show pr 12345", "pr body 12345", "details of pr 12345"
    pr_body_pattern = r'(?:show|get|fetch|details?|body|describe)\s+(?:pr|pull request)\s+#?(\d+)'
    match = re.search(pr_body_pattern, question_lower)
    if match:
        pr_id = int(match.group(1))
        print(f"\n📄 Fetching PR #{pr_id} details from filesystem...")
        
        conn = get_db_connection(SQLITE_PATH)
        pr_details = get_pr_body_tool(conn, pr_id, username)
        conn.close()
        
        return format_pr_body_response(pr_details)
    
    # Pattern 2: Show comment - "show comment 98765 on pr 12345"
    comment_pattern = r'(?:show|get|fetch)\s+comment\s+#?(\d+)\s+(?:on|for|in)\s+pr\s+#?(\d+)'
    match = re.search(comment_pattern, question_lower)
    if match:
        comment_id = int(match.group(1))
        pr_id = int(match.group(2))
        print(f"\n💬 Fetching comment #{comment_id} from PR #{pr_id}...")
        
        conn = get_db_connection(SQLITE_PATH)
        comment_details = get_comment_body_tool(conn, pr_id, comment_id, username)
        conn.close()
        
        return format_comment_response(comment_details)
    
    # Pattern 3: Show files - "show files in pr 12345", "what files changed in pr 12345"
    files_pattern = r'(?:show|get|fetch|what)\s+(?:files|changes|patches?)\s+(?:in|for|changed in)\s+pr\s+#?(\d+)'
    match = re.search(files_pattern, question_lower)
    if match:
        pr_id = int(match.group(1))
        print(f"\n📁 Fetching files for PR #{pr_id}...")
        
        conn = get_db_connection(SQLITE_PATH)
        files_list = get_pr_files_tool(conn, pr_id, username)
        conn.close()
        
        return format_files_response(files_list)
    
    # Pattern 4: Generate OKR update - multiple patterns
    # Pattern 4a: "generate update for X okr"
    okr_update_pattern = r'(?:generate|create|make)\s+(?:an?\s+)?update\s+for\s+(.+?)\s+(?:okr|goal)'
    match = re.search(okr_update_pattern, question_lower)
    
    # Pattern 4b: "get me the update for X" or "update for X in/from date"
    if not match:
        okr_update_pattern2 = r'(?:get(?:\s+me)?(?:\s+the)?|show(?:\s+me)?(?:\s+the)?|give(?:\s+me)?(?:\s+the)?)\s+update\s+for\s+(.+?)(?:\s+in\s+|\s+from\s+|\s+for\s+|$)'
        match = re.search(okr_update_pattern2, question_lower)
    
    # Pattern 4c: "okr update for X"
    if not match:
        okr_update_pattern3 = r'(?:okr|goal)\s+update\s+for\s+(.+?)(?:\s+in\s+|\s+from\s+|$)'
        match = re.search(okr_update_pattern3, question_lower)
    
    if match:
        okr_search = match.group(1).strip()
        
        # Remove date references from okr_search (e.g., "reserved ads in jan 2026" -> "reserved ads")
        okr_search = re.sub(r'\s+(?:in|from|for|during)\s+.*$', '', okr_search).strip()
        
        # Try to extract date range from question
        from datetime import datetime, timedelta
        
        # Pattern: "in jan 2026", "in january 2026", "from jan 2026"
        month_pattern = r'(?:in|from|for|during)\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{4})'
        month_match = re.search(month_pattern, question_lower)
        
        if month_match:
            month_abbr = month_match.group(1)
            year = month_match.group(2)
            
            # Map month abbreviations to numbers
            month_map = {
                'jan': '01', 'january': '01',
                'feb': '02', 'february': '02',
                'mar': '03', 'march': '03',
                'apr': '04', 'april': '04',
                'may': '05',
                'jun': '06', 'june': '06',
                'jul': '07', 'july': '07',
                'aug': '08', 'august': '08',
                'sep': '09', 'september': '09',
                'oct': '10', 'october': '10',
                'nov': '11', 'november': '11',
                'dec': '12', 'december': '12'
            }
            
            month_num = month_map.get(month_abbr, '01')
            start_date = f"{year}-{month_num}-01"
            
            # Calculate end date (last day of month)
            if month_num == '12':
                end_date = f"{year}-12-31"
            else:
                next_month = int(month_num) + 1
                end_date = f"{year}-{next_month:02d}-01"
        else:
            # Default to last 30 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        print(f"\n📊 Generating OKR update for '{okr_search}'...")
        print(f"   Date range: {start_date} to {end_date}")
        print(f"   This will:")
        print(f"   1. Find PRs matching OKR '{okr_search}' (by goal name OR category)")
        print(f"   2. Read PR bodies from filesystem")
        print(f"   3. Generate AI-powered technical & executive summaries")
        print()
        
        api_key = get_api_key()
        if not api_key:
            return "❌ Error: OpenAI API key not found. Cannot generate OKR update."
        
        conn = get_db_connection(SQLITE_PATH)
        try:
            updates = generate_okr_update_tool(
                conn,
                okr_search=okr_search,
                start_date=start_date,
                end_date=end_date,
                api_key=api_key
            )
            return format_okr_update_response(updates)
        finally:
            conn.close()
    
    return None


def interactive_mode(username: str):
    """Run agent in interactive mode."""
    # Import here after environment is set
    from app.config import SQLITE_PATH
    from app.tools_sqlite import db_doctor, get_schema
    from app.graph import run_agent
    
    print("=" * 80)
    print("PR Analytics Agent - Interactive Mode")
    print("=" * 80)
    print()
    print(f"Current user: {username}")
    print(f"Database: {SQLITE_PATH}")
    print()
    print("Commands:")
    print("  - Type your question and press Enter")
    print("  - Type 'doctor' to run diagnostics")
    print("  - Type 'schema' to see database schema")
    print("  - Type 'quit' or 'exit' to exit")
    print()
    print("Special Commands:")
    print("  - 'show pr 12345' - Show PR body and details from filesystem")
    print("  - 'show comment 98765 on pr 12345' - Show specific comment")
    print("  - 'show files in pr 12345' - Show all files changed with patches")
    print("  - 'get me the update for reserved ads in jan 2026' - Generate AI OKR update")
    print("  - 'generate update for resiliency okr' - Generate AI OKR update (last 30 days)")
    print()
    
    while True:
        try:
            question = input("❓ Ask a question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ["quit", "exit", "q"]:
                print("Goodbye! 👋")
                break
            
            if question.lower() == "doctor":
                print(db_doctor())
                continue
            
            if question.lower() == "schema":
                print(get_schema())
                continue
            
            # Check for special tool patterns
            special_result = handle_special_tools(question, username)
            if special_result:
                print(special_result)
                continue
            
            # Run standard agent
            print()
            state = run_agent(question, username)
            print()
            print_summary(state)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="PR Analytics Agent - Ask questions about your PR data"
    )
    
    parser.add_argument(
        "question",
        nargs="*",
        help="Question to ask (omit for interactive mode)"
    )
    
    parser.add_argument(
        "--base-dir",
        type=str,
        help="Base directory path (overrides FALCON_BASE_DIR env var and config)"
    )
    
    parser.add_argument(
        "--username",
        type=str,
        help="Username for queries (default: from settings file)"
    )
    
    parser.add_argument(
        "--db",
        type=Path,
        help="Path to database file (default: from config)"
    )
    
    parser.add_argument(
        "--doctor",
        action="store_true",
        help="Run database diagnostics"
    )
    
    parser.add_argument(
        "--schema",
        action="store_true",
        help="Show database schema"
    )
    
    parser.add_argument(
        "--no-sql",
        action="store_true",
        help="Don't show SQL query in output"
    )
    
    args = parser.parse_args()
    
    # Set base directory BEFORE importing config
    if args.base_dir:
        os.environ['FALCON_BASE_DIR'] = args.base_dir
    
    # NOW import config and other modules
    from app.config import DEFAULT_USERNAME, SQLITE_PATH
    from app.tools_sqlite import db_doctor, get_schema
    from app.graph import run_agent
    
    # Set username default
    username = args.username or DEFAULT_USERNAME
    
    # Override database path if provided
    if args.db:
        import app.config
        app.config.SQLITE_PATH = args.db
    
    # Handle doctor command
    if args.doctor:
        print(db_doctor(args.db))
        return 0
    
    # Handle schema command
    if args.schema:
        print(get_schema(args.db))
        return 0
    
    # Get question
    if args.question:
        question = " ".join(args.question)
        
        try:
            state = run_agent(question, username)
            print()
            print_summary(state, show_sql=not args.no_sql)
            return 0
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1
    else:
        # Interactive mode
        try:
            interactive_mode(username)
            return 0
        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main())
