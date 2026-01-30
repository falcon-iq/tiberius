#!/usr/bin/env python3
"""Main CLI entry point for PR Analytics Agent."""

import argparse
import sys
import os
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
            
            # Run agent
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
