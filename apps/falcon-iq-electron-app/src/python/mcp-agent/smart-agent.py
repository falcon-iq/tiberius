#!/usr/bin/env python3
"""
Smart MCP Agent with LangGraph
===============================

An intelligent agent that can reason through complex queries and orchestrate
multiple MCP tool calls to provide comprehensive answers.

Features:
- Natural language understanding
- Multi-step reasoning
- Tool orchestration
- Result synthesis
- Context awareness

Usage:
    python smart-agent.py "Show me bug comments from nhjain on resiliency PRs"
    python smart-agent.py --interactive
"""

import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, TypedDict, Annotated
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langgraph.graph import StateGraph, END
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Install with: pip install langgraph langchain-openai langchain-core")
    sys.exit(1)

# Import MCP tool wrappers
import os
from common import get_base_dir, getDBPath, load_all_config, get_openai_api_key
from prDataReader import get_pr_details, get_comment_details, get_pr_files
from readOKRs import findByOkrName, findByOkrNameWithDetails, read_okrs_from_db
from readUsers import read_users_from_db
from generateOKRUpdate import find_prs_by_okr_and_dates, collect_pr_bodies, generate_updates_with_openai


# Helper function to get API key from config or environment
def get_openai_api_key_from_config_or_env() -> str:
    """
    Get OpenAI API key from config file or environment variable.
    
    Priority:
    1. Try loading from settings.json via load_all_config()
    2. Fall back to OPENAI_API_KEY environment variable
    
    Returns:
        OpenAI API key
        
    Raises:
        ValueError: If API key not found in config or environment
    """
    try:
        # Try to load from config file
        all_config = load_all_config()
        settings = all_config.get('settings', {})
        api_key = get_openai_api_key(settings)
        
        if api_key:
            return api_key
    except Exception as e:
        # If config loading fails, try environment variable
        pass
    
    # Fall back to environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    
    raise ValueError(
        "OpenAI API key not found. Please either:\n"
        "1. Set it in your settings.json file (openai_api_key field), OR\n"
        "2. Set OPENAI_API_KEY environment variable"
    )


# State definition
class AgentState(TypedDict):
    """State for the smart agent."""
    query: str
    plan: str
    tool_calls: List[Dict[str, Any]]
    results: List[Dict[str, Any]]
    final_answer: str
    error: str
    iterations: int


# Tool registry
class MCPTools:
    """Registry of available MCP tools."""
    
    def __init__(self):
        self.base_dir = get_base_dir()
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """
        Get database connection with Row factory.
        Creates a new connection each time to avoid SQLite threading issues.
        """
        base_dir = get_base_dir()
        db_path = getDBPath(base_dir)
        # check_same_thread=False allows connection to be used across threads
        # Safe here because we create new connections per request
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Return list of available tools with descriptions."""
        return [
            {
                "name": "get_pr_details",
                "description": "Get detailed information about a specific PR including title, body, author, stats",
                "parameters": "pr_id (required), username (optional)"
            },
            {
                "name": "get_comment_details",
                "description": "Get details of a specific comment on a PR",
                "parameters": "pr_id (required), comment_id (required), username (optional)"
            },
            {
                "name": "get_pr_files",
                "description": "Get all file changes in a PR with patches",
                "parameters": "pr_id (required), username (optional)"
            },
            {
                "name": "search_okrs",
                "description": "Search for OKRs by name or keyword",
                "parameters": "search_term (required), with_details (optional)"
            },
            {
                "name": "list_all_okrs",
                "description": "Get a list of all OKRs in the system",
                "parameters": "username (optional)"
            },
            {
                "name": "generate_okr_update",
                "description": "Generate AI-powered updates for an OKR based on PRs",
                "parameters": "okr_search (required), start_date (required), end_date (required), usernames (optional)"
            },
            {
                "name": "find_prs_by_okr",
                "description": "Find all PRs related to a specific OKR within a date range",
                "parameters": "okr_search (required), start_date (required), end_date (required), usernames (optional)"
            },
            {
                "name": "list_all_users",
                "description": "Get a list of all users in the system",
                "parameters": "none"
            },
            {
                "name": "query_users",
                "description": "Execute custom SQL query on users table",
                "parameters": "sql_query (required)"
            },
            {
                "name": "query_review_comments",
                "description": "Query and analyze code review comments with signal classifications. Available signals: is_nitpick, mentions_tests, mentions_bug, mentions_design, mentions_performance, mentions_reliability, mentions_security. Use exact signal names for filtering.",
                "parameters": "username, filter_by_signals (use exact signal names like 'mentions_bug'), filter_by_category, filter_by_pr, group_by, include_details, limit"
            },
            {
                "name": "query_pr_stats",
                "description": "Execute SQL query on pr_stats table for PR analytics",
                "parameters": "Custom SQL query on pr_stats and pr_comment_details tables"
            }
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return results."""
        # Create a fresh database connection for this tool execution
        # This avoids SQLite threading issues
        db_conn = self._get_db_connection()
        
        try:
            if tool_name == "list_all_users":
                users = read_users_from_db(db_conn)
                return {"success": True, "data": users}
            
            elif tool_name == "search_okrs":
                search_term = arguments.get("search_term")
                with_details = arguments.get("with_details", True)
                
                if with_details:
                    from readOKRs import findByOkrNameWithDetails
                    okrs = findByOkrNameWithDetails(db_conn, search_term)
                else:
                    okr_ids = findByOkrName(db_conn, search_term)
                    okrs = okr_ids
                
                return {"success": True, "data": okrs}
            
            elif tool_name == "list_all_okrs":
                okrs = read_okrs_from_db(db_conn)
                return {"success": True, "data": okrs}
            
            elif tool_name == "find_prs_by_okr":
                okr_search = arguments.get("okr_search")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                usernames = arguments.get("usernames")
                
                # Find OKR IDs
                okr_ids = findByOkrName(db_conn, okr_search)
                
                # Find PRs (note: correct parameter order is conn, okr_ids, category_search, start_date, end_date, usernames)
                prs = find_prs_by_okr_and_dates(
                    conn=db_conn,
                    okr_ids=okr_ids,
                    category_search=okr_search if not okr_ids else None,
                    start_date=start_date,
                    end_date=end_date,
                    usernames=usernames
                )
                
                return {"success": True, "data": prs, "okr_ids": okr_ids}
            
            elif tool_name == "query_review_comments":
                # Build query based on arguments
                query_parts = ["SELECT"]
                
                group_by = arguments.get("group_by")
                include_details = arguments.get("include_details", False)
                limit = arguments.get("limit", 100)
                
                if group_by == "signal":
                    # Get signal distribution
                    signals = {}
                    cursor = db_conn.cursor()
                    cursor.execute("SELECT SUM(is_nitpick) as nitpick, SUM(mentions_tests) as tests, "
                                 "SUM(mentions_bug) as bug, SUM(mentions_design) as design, "
                                 "SUM(mentions_performance) as performance, SUM(mentions_reliability) as reliability, "
                                 "SUM(mentions_security) as security FROM pr_comment_details")
                    row = cursor.fetchone()
                    signals = dict(row)
                    return {"success": True, "data": signals}
                
                elif group_by:
                    cursor = db_conn.cursor()
                    if group_by == "category":
                        cursor.execute(f"SELECT primary_category, COUNT(*) as count FROM pr_comment_details "
                                     f"GROUP BY primary_category ORDER BY count DESC LIMIT {limit}")
                    elif group_by == "severity":
                        cursor.execute(f"SELECT severity, COUNT(*) as count FROM pr_comment_details "
                                     f"GROUP BY severity ORDER BY count DESC LIMIT {limit}")
                    elif group_by == "pr_author":
                        cursor.execute(f"SELECT pr_author, COUNT(*) as count FROM pr_comment_details "
                                     f"GROUP BY pr_author ORDER BY count DESC LIMIT {limit}")
                    
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    return {"success": True, "data": results}
                
                else:
                    # Build filtered query
                    where_clauses = []
                    params = []
                    
                    if arguments.get("username"):
                        where_clauses.append("username = ?")
                        params.append(arguments["username"])
                    
                    # Handle filter_by_signals - can be dict or string
                    filter_by_signals = arguments.get("filter_by_signals")
                    if filter_by_signals:
                        if isinstance(filter_by_signals, dict):
                            # Dict format: {"mentions_bug": true, "is_nitpick": true}
                            for signal, value in filter_by_signals.items():
                                if value:
                                    where_clauses.append(f"{signal} = 1")
                        elif isinstance(filter_by_signals, str):
                            # String format: "mentions_bug"
                            where_clauses.append(f"{filter_by_signals} = 1")
                        elif isinstance(filter_by_signals, list):
                            # List format: ["mentions_bug", "mentions_performance"]
                            for signal in filter_by_signals:
                                where_clauses.append(f"{signal} = 1")
                    
                    if arguments.get("filter_by_category"):
                        where_clauses.append("primary_category LIKE ?")
                        params.append(f"%{arguments['filter_by_category']}%")
                    
                    if arguments.get("filter_by_pr"):
                        where_clauses.append("pr_number = ?")
                        params.append(arguments["filter_by_pr"])
                    
                    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
                    
                    if include_details:
                        query = f"SELECT * FROM pr_comment_details WHERE {where_clause} LIMIT {limit}"
                    else:
                        query = f"SELECT pr_number, comment_id, username, primary_category, severity FROM pr_comment_details WHERE {where_clause} LIMIT {limit}"
                    
                    cursor = db_conn.cursor()
                    cursor.execute(query, params)
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    
                    return {"success": True, "data": results}
            
            elif tool_name == "get_pr_details":
                pr_id = arguments.get("pr_id")
                username = arguments.get("username")
                details = get_pr_details(db_conn, pr_id, username, self.base_dir)
                return {"success": True, "data": details}
            
            elif tool_name == "get_pr_files":
                pr_id = arguments.get("pr_id")
                username = arguments.get("username")
                files = get_pr_files(db_conn, pr_id, username, self.base_dir)
                return {"success": True, "data": files}
            
            elif tool_name == "get_comment_details":
                pr_id = arguments.get("pr_id")
                comment_id = arguments.get("comment_id")
                username = arguments.get("username")
                comment = get_comment_details(db_conn, pr_id, comment_id, username, self.base_dir)
                return {"success": True, "data": comment}
            
            elif tool_name == "generate_okr_update":
                okr_search = arguments.get("okr_search")
                start_date = arguments.get("start_date")
                end_date = arguments.get("end_date")
                usernames = arguments.get("usernames")
                
                # Find OKR IDs
                okr_ids = findByOkrName(db_conn, okr_search)
                
                if not okr_ids:
                    return {"success": False, "error": f"No OKRs found matching: {okr_search}"}
                
                # Find PRs (note: correct parameter order is conn, okr_ids, category_search, start_date, end_date, usernames)
                prs = find_prs_by_okr_and_dates(
                    conn=db_conn,
                    okr_ids=okr_ids,
                    category_search=okr_search if not okr_ids else None,
                    start_date=start_date,
                    end_date=end_date,
                    usernames=usernames
                )
                
                if not prs:
                    return {"success": True, "data": {"message": f"No PRs found for OKR '{okr_search}' in the given date range.", "prs": []}}
                
                # Collect PR bodies
                pr_details = collect_pr_bodies(db_conn, prs, self.base_dir)
                
                # Generate updates with OpenAI
                api_key = get_openai_api_key_from_config_or_env()
                # Note: function signature is generate_updates_with_openai(pr_details_list, okr_search, api_key)
                updates = generate_updates_with_openai(
                    pr_details_list=pr_details,
                    okr_search=okr_search,
                    api_key=api_key
                )
                
                return {
                    "success": True, 
                    "data": {
                        "okr_name": okr_search,
                        "okr_ids": okr_ids,
                        "pr_count": len(prs),
                        "prs": prs,
                        "updates": updates
                    }
                }
            
            elif tool_name == "query_pr_stats":
                sql_query = arguments.get("sql_query")
                if not sql_query:
                    return {"success": False, "error": "sql_query parameter is required"}
                
                # Basic SQL safety check
                sql_upper = sql_query.upper().strip()
                if not sql_upper.startswith("SELECT"):
                    return {"success": False, "error": "Only SELECT queries are allowed"}
                
                dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
                if any(keyword in sql_upper for keyword in dangerous_keywords):
                    return {"success": False, "error": "Query contains dangerous keywords"}
                
                cursor = db_conn.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                
                return {"success": True, "data": results}
            
            elif tool_name == "query_users":
                sql_query = arguments.get("sql_query")
                if not sql_query:
                    return {"success": False, "error": "sql_query parameter is required"}
                
                # Basic SQL safety check
                sql_upper = sql_query.upper().strip()
                if not sql_upper.startswith("SELECT"):
                    return {"success": False, "error": "Only SELECT queries are allowed"}
                
                dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE"]
                if any(keyword in sql_upper for keyword in dangerous_keywords):
                    return {"success": False, "error": "Query contains dangerous keywords"}
                
                cursor = db_conn.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                
                return {"success": True, "data": results}
            
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
        
        finally:
            # Always close the database connection
            if 'db_conn' in locals():
                db_conn.close()


class SmartAgent:
    """Smart agent that can reason and orchestrate MCP tools."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=get_openai_api_key_from_config_or_env()
        )
        self.tools = MCPTools()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("executor", self._executor_node)
        workflow.add_node("synthesizer", self._synthesizer_node)
        
        # Add edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "synthesizer")
        workflow.add_edge("synthesizer", END)
        
        return workflow.compile()
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Plan which tools to use and in what order."""
        query = state["query"]
        
        # Get available tools
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']} (params: {t['parameters']})"
            for t in self.tools.get_available_tools()
        ])
        
        system_prompt = f"""You are a planning agent that breaks down complex queries into tool calls.

Available tools:
{tools_desc}

Your job is to:
1. Understand the user's question
2. Break it down into a sequence of tool calls
3. Return a JSON plan with the tools to call and their arguments

Return ONLY a JSON object with this structure:
{{
  "reasoning": "brief explanation of your plan",
  "tool_calls": [
    {{"tool": "tool_name", "arguments": {{}}, "purpose": "why calling this"}}
  ]
}}
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User query: {query}")
        ]
        
        response = self.llm.invoke(messages)
        
        try:
            # Extract JSON from response
            content = response.content
            # Find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != 0:
                plan_json = json.loads(content[start:end])
                state["plan"] = plan_json.get("reasoning", "")
                state["tool_calls"] = plan_json.get("tool_calls", [])
            else:
                state["error"] = "Could not parse plan from LLM response"
        except Exception as e:
            state["error"] = f"Error parsing plan: {str(e)}"
        
        return state
    
    def _executor_node(self, state: AgentState) -> AgentState:
        """Execute the planned tool calls."""
        results = []
        
        for tool_call in state.get("tool_calls", []):
            tool_name = tool_call.get("tool")
            arguments = tool_call.get("arguments", {})
            
            print(f"🔧 Executing: {tool_name} with {arguments}")
            
            result = self.tools.execute_tool(tool_name, arguments)
            results.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })
        
        state["results"] = results
        return state
    
    def _synthesizer_node(self, state: AgentState) -> AgentState:
        """Synthesize final answer from results."""
        query = state["query"]
        plan = state.get("plan", "")
        results = state.get("results", [])
        
        # Format results for LLM
        results_text = "\n\n".join([
            f"Tool: {r['tool']}\nArguments: {json.dumps(r['arguments'])}\n"
            f"Result: {json.dumps(r['result'], indent=2, default=str)}"
            for r in results
        ])
        
        system_prompt = """You are an assistant that synthesizes information from multiple tool calls.

Given the user's original question, the plan, and the results from tool executions,
provide a clear, comprehensive answer.

Format your answer in a user-friendly way with:
- Clear headings
- Bullet points or tables where appropriate
- Summary statistics
- Key insights
"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""Original query: {query}

Plan: {plan}

Tool execution results:
{results_text}

Please provide a comprehensive answer to the user's question based on these results.""")
        ]
        
        response = self.llm.invoke(messages)
        state["final_answer"] = response.content
        
        return state
    
    def run(self, query: str) -> str:
        """Run the agent on a query."""
        print(f"\n🤖 Processing query: {query}\n")
        
        initial_state = {
            "query": query,
            "plan": "",
            "tool_calls": [],
            "results": [],
            "final_answer": "",
            "error": "",
            "iterations": 0
        }
        
        final_state = self.graph.invoke(initial_state)
        
        if final_state.get("error"):
            return f"Error: {final_state['error']}"
        
        return final_state.get("final_answer", "No answer generated")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart MCP Agent with LangGraph")
    parser.add_argument("query", nargs="?", help="Query to process")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    agent = SmartAgent()
    
    if args.interactive:
        print("🤖 Smart MCP Agent - Interactive Mode")
        print("=" * 60)
        print("Type your questions or 'exit' to quit.")
        print()
        
        while True:
            try:
                query = input("\n💭 Your question: ").strip()
                
                if query.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break
                
                if not query:
                    continue
                
                answer = agent.run(query)
                print(f"\n📝 Answer:\n{answer}\n")
                print("=" * 60)
            
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    elif args.query:
        answer = agent.run(args.query)
        print(f"\n📝 Answer:\n{answer}\n")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
