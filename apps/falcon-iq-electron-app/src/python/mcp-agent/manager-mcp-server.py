#!/usr/bin/env python3
"""
Manager MCP Server
==================

A Model Context Protocol (MCP) server that provides tools for managing PR analytics,
OKR tracking, and team collaboration insights.

This server exposes:
- PR analytics tools (query, search, analyze)
- OKR management tools (read, search, generate updates)
- Data reading tools (PR details, comments, files)
- AI-powered summarization tools

Usage:
    python manager-mcp-server.py

Environment Variables:
    FALCON_BASE_DIR: Base directory for data storage
    OPENAI_API_KEY: OpenAI API key for AI-powered features
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
    import mcp.server.stdio
except ImportError:
    print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import our existing modules
from common import get_base_dir, getDBPath, get_openai_api_key, set_base_dir
from prDataReader import get_pr_details, get_comment_details, get_pr_files
from readOKRs import findByOkrName, findByOkrNameWithDetails, read_okrs_from_db
from readUsers import read_users_from_db
from generateOKRUpdate import (
    find_prs_by_okr_and_dates,
    collect_pr_bodies,
    generate_updates_with_openai
)
import sqlite3

# Initialize the MCP server
app = Server("falcon-iq-manager")


def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    base_dir = get_base_dir()
    db_path = getDBPath(base_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="get_pr_details",
            description=(
                "Get detailed information about a specific Pull Request from the filesystem. This contains metadata information about the PR committed by the user."
                "Returns comprehensive PR metadata including: owner, repo, pr_number, pr_title, pr_body, "
                "pr_state, pr_draft, pr_author, pr_created_at, pr_updated_at, pr_merged_at, pr_mergeable_state, "
                "pr_additions, pr_deletions, pr_changed_files, pr_commits_count, pr_issue_comments_count, "
                "pr_review_comments_count, and pr_html_url. Use this to read the full PR description, "
                "understand changes, and analyze PR additional information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "integer",
                        "description": "The PR ID to retrieve details for"
                    },
                    "username": {
                        "type": "string",
                        "description": "Optional username filter"
                    }
                },
                "required": ["pr_id"]
            }
        ),
        Tool(
            name="get_comment_details",
            description=(
                "Get details of a specific comment on a Pull Request from the filesystem. "
                "Returns comment data including: owner, repo, pr_number, comment_type (issue_comment or review_comment), "
                "comment_id, user, created_at, body, state, is_reviewer (boolean), path (for review comments) "
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "integer",
                        "description": "The PR ID"
                    },
                    "comment_id": {
                        "type": "integer",
                        "description": "The comment ID to retrieve"
                    },
                    "username": {
                        "type": "string",
                        "description": "Optional username filter"
                    }
                },
                "required": ["pr_id", "comment_id"]
            }
        ),
        Tool(
            name="get_pr_files",
            description=(
                "Get all file changes in a Pull Request from the filesystem. "
                "Returns a list of changed files with data including: owner, repo, pr_number, filename, "
                "status (added/modified/deleted/renamed), additions, deletions, changes (total line changes), "
                "blob_url, raw_url, and patch (the actual diff content showing line-by-line changes). "
                "Use this to understand what code was changed, review diffs, and analyze the scope of modifications."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "pr_id": {
                        "type": "integer",
                        "description": "The PR ID to get files for"
                    },
                    "username": {
                        "type": "string",
                        "description": "Optional username filter"
                    }
                },
                "required": ["pr_id"]
            }
        ),
        Tool(
            name="search_okrs",
            description="Search for OKRs by name or keyword using LIKE query",
            inputSchema={
                "type": "object",
                "properties": {
                    "search_term": {
                        "type": "string",
                        "description": "Search term to find in OKR names (case-insensitive, partial match)"
                    },
                    "with_details": {
                        "type": "boolean",
                        "description": "Whether to return full OKR details or just IDs",
                        "default": True
                    }
                },
                "required": ["search_term"]
            }
        ),
        Tool(
            name="list_all_okrs",
            description="Get a list of all OKRs in the system with their details",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Optional username filter to get OKRs for specific user"
                    }
                }
            }
        ),
        Tool(
            name="generate_okr_update",
            description="Generate AI-powered technical and executive updates for an OKR based on related PRs",
            inputSchema={
                "type": "object",
                "properties": {
                    "okr_search": {
                        "type": "string",
                        "description": "OKR name or keyword to search for"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for PR filtering (YYYY-MM-DD format)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for PR filtering (YYYY-MM-DD format)"
                    },
                    "category_search": {
                        "type": "string",
                        "description": "Optional category search term if OKR not found"
                    },
                    "usernames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of usernames to filter PRs"
                    }
                },
                "required": ["okr_search", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_pr_stats",
            description=(
                "Query code review and PR statistics from the database. Analyzes both authored and reviewed PRs. "
                "\n\nDatabase Schema:\n"
                "pr_stats table columns: username, pr_id, reviewed_authored ('authored'|'reviewed'), goal_id, "
                "category, created_time, confidence, author_of_pr, repo, is_ai_author\n"
                "pr_comment_details table columns: pr_number, comment_id, username, comment_type, created_at, "
                "is_reviewer, pr_author, primary_category, secondary_categories, severity, confidence, "
                "actionability, is_nitpick, mentions_tests, mentions_bug, mentions_design, mentions_performance, "
                "mentions_reliability, mentions_security\n"
                "\n\nUseful for questions like:\n"
                "- 'How many PRs did I review for John?' (reviews by author)\n"
                "- 'Who did I review the most PRs for?' (top reviewed authors)\n"
                "- 'Show me authors where I left more than 10 comments' (comment statistics)\n"
                "- 'What is my average comments per PR?' (comment averages)\n"
                "- 'How many PRs did I author vs review?' (authored vs reviewed)\n"
                "- 'What PRs are linked to X OKR?' (OKR tracking)\n"
                "- 'Show PRs in X category/repo' (filtering by category/repo)\n"
                "- 'What are my review comment categories?' (comment analysis)\n"
                "\n\nReturns aggregated statistics about PRs authored, PRs reviewed, authors, comments, categories, and OKRs."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language question about PRs, reviews, or comments"
                    },
                    "username": {
                        "type": "string",
                        "description": "Optional username for filtering (use 'me' for current user)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="find_prs_by_okr",
            description="Find all PRs related to a specific OKR within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "okr_search": {
                        "type": "string",
                        "description": "OKR name or keyword to search for"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date (YYYY-MM-DD)"
                    },
                    "usernames": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of usernames to filter"
                    }
                },
                "required": ["okr_search", "start_date", "end_date"]
            }
        ),
        Tool(
            name="list_all_users",
            description=(
                "Get a list of all users from the database. "
                "Returns user data including: username, github_suffix, email_address, firstname, lastname. "
                "Also provides computed fields: prUserName (userName_githubSuffix). "
                "Use this to get team member information, find GitHub usernames, or list all users."
            ),
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="query_users",
            description=(
                "Execute a custom SQL query on the users table. "
                "The users table has columns: username, github_suffix, email_address, firstname, lastname. "
                "Use this to search for specific users, filter by criteria, or aggregate user data. "
                "Query must be a valid SELECT statement. For safety, only SELECT queries are allowed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "SQL SELECT query to execute on the users table (e.g., 'SELECT * FROM users WHERE username LIKE \"%smith%\"')"
                    }
                },
                "required": ["sql_query"]
            }
        ),
        Tool(
            name="query_review_comments",
            description=(
                "Query and analyze code review comments with signal classifications. "
                "The pr_comment_details table contains: pr_number, comment_id, username, comment_type, created_at, "
                "is_reviewer, line, side, pr_author, primary_category, secondary_categories, severity, confidence, "
                "actionability, rationale, is_ai_reviewer, is_nitpick, mentions_tests, mentions_bug, mentions_design, "
                "mentions_performance, mentions_reliability, mentions_security. "
                "\n\nUseful for questions like:\n"
                "- 'How many comments did I make about performance?'\n"
                "- 'Show me all my bug-related comments'\n"
                "- 'What is my comment breakdown by category?'\n"
                "- 'How many nitpick comments did I make?'\n"
                "- 'Show security-related comments in repository X'\n"
                "- 'What are my most severe comments?'\n"
                "\n\nSupports filtering by signals (is_nitpick, mentions_tests, mentions_bug, mentions_design, "
                "mentions_performance, mentions_reliability, mentions_security), category, repo, or PR number. "
                "Can group results and optionally include detailed comment information."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Filter by username (comment author)"
                    },
                    "filter_by_signals": {
                        "type": "object",
                        "description": "Filter by signal flags (set desired signals to true)",
                        "properties": {
                            "is_nitpick": {"type": "boolean", "description": "Nitpick/minor comments"},
                            "mentions_tests": {"type": "boolean", "description": "Comments about tests"},
                            "mentions_bug": {"type": "boolean", "description": "Comments about bugs"},
                            "mentions_design": {"type": "boolean", "description": "Comments about design"},
                            "mentions_performance": {"type": "boolean", "description": "Comments about performance"},
                            "mentions_reliability": {"type": "boolean", "description": "Comments about reliability"},
                            "mentions_security": {"type": "boolean", "description": "Comments about security"}
                        }
                    },
                    "filter_by_category": {
                        "type": "string",
                        "description": "Filter by primary category (substring match)"
                    },
                    "filter_by_pr": {
                        "type": "integer",
                        "description": "Filter by specific PR number"
                    },
                    "group_by": {
                        "type": "string",
                        "enum": ["signal", "pr", "category", "severity", "pr_author"],
                        "description": "Group results by field (signal, pr, category, severity, or pr_author)"
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "Include detailed comment information (default: false)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Limit number of results (default: 100)"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    """Handle tool calls."""
    try:
        base_dir = get_base_dir()
        db_conn = get_db_connection()
        
        if name == "get_pr_details":
            pr_id = arguments["pr_id"]
            username = arguments.get("username")
            
            result = get_pr_details(
                db_conn=db_conn,
                pr_id=pr_id,
                username=username,
                base_dir=base_dir
            )
            
            if result:
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"PR {pr_id} not found"
                )]
        
        elif name == "get_comment_details":
            pr_id = arguments["pr_id"]
            comment_id = arguments["comment_id"]
            username = arguments.get("username")
            
            result = get_comment_details(
                db_conn=db_conn,
                pr_id=pr_id,
                comment_id=comment_id,
                username=username,
                base_dir=base_dir
            )
            
            if result:
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Comment {comment_id} on PR {pr_id} not found"
                )]
        
        elif name == "get_pr_files":
            pr_id = arguments["pr_id"]
            username = arguments.get("username")
            
            result = get_pr_files(
                db_conn=db_conn,
                pr_id=pr_id,
                username=username,
                base_dir=base_dir
            )
            
            if result:
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"No files found for PR {pr_id}"
                )]
        
        elif name == "search_okrs":
            search_term = arguments["search_term"]
            with_details = arguments.get("with_details", True)
            
            if with_details:
                result = findByOkrNameWithDetails(db_conn, search_term)
            else:
                result = findByOkrName(db_conn, search_term)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        
        elif name == "list_all_okrs":
            username = arguments.get("username")
            # Note: read_okrs_from_db doesn't support username filtering
            # It returns all OKRs in the system
            result = read_okrs_from_db(db_conn)
            
            # If username was provided, we could filter client-side here if needed
            # For now, just return all OKRs
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        
        elif name == "generate_okr_update":
            okr_search = arguments["okr_search"]
            start_date = arguments["start_date"]
            end_date = arguments["end_date"]
            category_search = arguments.get("category_search")
            usernames = arguments.get("usernames")
            
            # Get API key
            api_key = get_openai_api_key()
            if not api_key:
                return [TextContent(
                    type="text",
                    text="Error: OPENAI_API_KEY not configured"
                )]
            
            # Find OKR IDs
            okr_ids = findByOkrName(db_conn, okr_search)
            
            # Find PRs
            prs = find_prs_by_okr_and_dates(
                db_conn=db_conn,
                okr_ids=okr_ids,
                start_date=start_date,
                end_date=end_date,
                category_search=category_search if not okr_ids else None,
                usernames=usernames
            )
            
            if not prs:
                return [TextContent(
                    type="text",
                    text=f"No PRs found for '{okr_search}' between {start_date} and {end_date}"
                )]
            
            # Collect PR bodies
            pr_details_list = collect_pr_bodies(db_conn, prs, base_dir)
            
            # Generate updates with OpenAI
            updates = generate_updates_with_openai(
                pr_details_list=pr_details_list,
                okr_search=okr_search,
                api_key=api_key
            )
            
            result = {
                "okr_search": okr_search,
                "date_range": f"{start_date} to {end_date}",
                "pr_count": len(prs),
                "technical_update": updates["technical_update"],
                "executive_update": updates["executive_update"]
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "query_pr_stats":
            # This would integrate with the PR Analytics Agent
            query = arguments["query"]
            username = arguments.get("username")
            
            return [TextContent(
                type="text",
                text=f"PR Analytics Agent integration coming soon for query: {query}"
            )]
        
        elif name == "find_prs_by_okr":
            okr_search = arguments["okr_search"]
            start_date = arguments["start_date"]
            end_date = arguments["end_date"]
            usernames = arguments.get("usernames")
            
            # Find OKR IDs
            okr_ids = findByOkrName(db_conn, okr_search)
            
            # Find PRs
            prs = find_prs_by_okr_and_dates(
                db_conn=db_conn,
                okr_ids=okr_ids,
                start_date=start_date,
                end_date=end_date,
                category_search=okr_search if not okr_ids else None,
                usernames=usernames
            )
            
            result = {
                "okr_search": okr_search,
                "date_range": f"{start_date} to {end_date}",
                "pr_count": len(prs),
                "prs": prs
            }
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]
        
        elif name == "list_all_users":
            # Get all users from database
            users = read_users_from_db(db_conn)
            
            return [TextContent(
                type="text",
                text=json.dumps(users, indent=2)
            )]
        
        elif name == "query_users":
            sql_query = arguments["sql_query"].strip()
            
            # Safety check: Only allow SELECT queries
            if not sql_query.upper().startswith("SELECT"):
                return [TextContent(
                    type="text",
                    text="Error: Only SELECT queries are allowed for security reasons"
                )]
            
            # Additional safety: Block dangerous keywords
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
            upper_query = sql_query.upper()
            for keyword in dangerous_keywords:
                if keyword in upper_query:
                    return [TextContent(
                        type="text",
                        text=f"Error: Query contains forbidden keyword: {keyword}"
                    )]
            
            try:
                cursor = db_conn.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                
                # Convert rows to list of dicts
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "query": sql_query,
                        "row_count": len(results),
                        "results": results
                    }, indent=2)
                )]
            except sqlite3.Error as e:
                return [TextContent(
                    type="text",
                    text=f"SQL Error: {str(e)}"
                )]
        
        elif name == "query_review_comments":
            username = arguments.get("username")
            filter_by_signals = arguments.get("filter_by_signals", {})
            filter_by_category = arguments.get("filter_by_category")
            filter_by_pr = arguments.get("filter_by_pr")
            group_by = arguments.get("group_by")
            include_details = arguments.get("include_details", False)
            limit = arguments.get("limit", 100)
            
            # Build the query
            query_parts = ["SELECT"]
            
            if group_by:
                # Grouped query
                if group_by == "signal":
                    query_parts.append("""
                        'is_nitpick' as signal_type, SUM(is_nitpick) as count
                        FROM pr_comment_details WHERE 1=1
                    """)
                elif group_by == "pr":
                    query_parts.append("""
                        pr_number, COUNT(*) as comment_count
                        FROM pr_comment_details WHERE 1=1
                    """)
                elif group_by == "category":
                    query_parts.append("""
                        primary_category, COUNT(*) as count
                        FROM pr_comment_details WHERE 1=1
                    """)
                elif group_by == "severity":
                    query_parts.append("""
                        severity, COUNT(*) as count
                        FROM pr_comment_details WHERE 1=1
                    """)
                elif group_by == "pr_author":
                    query_parts.append("""
                        pr_author, COUNT(*) as comment_count
                        FROM pr_comment_details WHERE 1=1
                    """)
            else:
                # Detail query
                if include_details:
                    query_parts.append("* FROM pr_comment_details WHERE 1=1")
                else:
                    query_parts.append("""
                        pr_number, comment_id, username, primary_category, severity, 
                        is_nitpick, mentions_tests, mentions_bug, mentions_design,
                        mentions_performance, mentions_reliability, mentions_security
                        FROM pr_comment_details WHERE 1=1
                    """)
            
            params = []
            where_parts = []
            
            # Apply filters
            if username:
                where_parts.append("username = ?")
                params.append(username)
            
            if filter_by_signals:
                for signal, value in filter_by_signals.items():
                    if value is True:
                        where_parts.append(f"{signal} = 1")
            
            if filter_by_category:
                where_parts.append("primary_category LIKE ?")
                params.append(f"%{filter_by_category}%")
            
            if filter_by_pr:
                where_parts.append("pr_number = ?")
                params.append(filter_by_pr)
            
            # Combine query
            full_query = " ".join(query_parts)
            if where_parts:
                full_query += " AND " + " AND ".join(where_parts)
            
            # Add GROUP BY if needed
            if group_by:
                if group_by == "signal":
                    # Special handling for signal grouping
                    full_query = f"""
                        SELECT 'is_nitpick' as signal_type, SUM(is_nitpick) as count FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_tests', SUM(mentions_tests) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_bug', SUM(mentions_bug) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_design', SUM(mentions_design) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_performance', SUM(mentions_performance) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_reliability', SUM(mentions_reliability) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        UNION ALL
                        SELECT 'mentions_security', SUM(mentions_security) FROM pr_comment_details WHERE 1=1 {' AND ' + ' AND '.join(where_parts) if where_parts else ''}
                        ORDER BY count DESC
                    """
                elif group_by == "pr":
                    full_query += " GROUP BY pr_number ORDER BY comment_count DESC"
                elif group_by == "category":
                    full_query += " GROUP BY primary_category ORDER BY count DESC"
                elif group_by == "severity":
                    full_query += " GROUP BY severity ORDER BY count DESC"
                elif group_by == "pr_author":
                    full_query += " GROUP BY pr_author ORDER BY comment_count DESC"
            else:
                full_query += " ORDER BY pr_number DESC, comment_id DESC"
            
            # Add limit
            full_query += f" LIMIT {limit}"
            
            try:
                cursor = db_conn.cursor()
                cursor.execute(full_query, params)
                rows = cursor.fetchall()
                
                # Convert rows to list of dicts
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                
                # Build summary
                summary = {
                    "total_results": len(results),
                    "filters_applied": {
                        "username": username,
                        "signals": filter_by_signals if filter_by_signals else None,
                        "category": filter_by_category,
                        "pr_number": filter_by_pr
                    },
                    "grouped_by": group_by,
                    "limit": limit
                }
                
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "summary": summary,
                        "results": results
                    }, indent=2, default=str)
                )]
            except sqlite3.Error as e:
                return [TextContent(
                    type="text",
                    text=f"SQL Error: {str(e)}\nQuery: {full_query}"
                )]
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Error executing {name}: {str(e)}"
        )]
    finally:
        if 'db_conn' in locals():
            db_conn.close()


async def main():
    """Main entry point for the MCP server."""
    # Read server options from stdin
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("Starting Falcon IQ Manager MCP Server...", file=sys.stderr)
    asyncio.run(main())
