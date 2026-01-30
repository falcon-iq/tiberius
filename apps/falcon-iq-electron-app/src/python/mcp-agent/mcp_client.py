#!/usr/bin/env python3
"""
Simple MCP Client for Falcon IQ Manager
=========================================

A command-line client for querying the MCP server.

Usage:
    python mcp_client.py list_all_users
    python mcp_client.py search_okrs '{"search_term": "resiliency"}'
    python mcp_client.py get_pr_details '{"pr_id": 12345}'
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Get the script directory
SCRIPT_DIR = Path(__file__).parent
SERVER_PATH = SCRIPT_DIR / "manager-mcp-server.py"


def call_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict]:
    """
    Call an MCP tool and return the result.
    
    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments as a dictionary
    
    Returns:
        Tool result or None if error
    """
    
    # Prepare the MCP protocol messages
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "python-client", "version": "1.0"}
        }
    }
    
    tool_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }
    
    # Combine messages
    input_data = json.dumps(init_msg) + "\n" + json.dumps(tool_msg)
    
    # Call the MCP server
    try:
        result = subprocess.run(
            ["python3", str(SERVER_PATH)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30
        )
    except subprocess.TimeoutExpired:
        print("Error: Request timed out after 30 seconds", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error calling MCP server: {e}", file=sys.stderr)
        return None
    
    # Parse the response (get the second JSON response)
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if line.startswith('{"jsonrpc'):
            try:
                response = json.loads(line)
                if response.get('id') == 2:
                    result_data = response.get('result', {})
                    if result_data.get('isError'):
                        content = result_data.get('content', [{}])[0].get('text', 'Unknown error')
                        print(f"Error: {content}", file=sys.stderr)
                        return None
                    return result_data
            except json.JSONDecodeError:
                continue
    
    # Check for errors in stderr
    if result.stderr:
        print(f"Server stderr: {result.stderr}", file=sys.stderr)
    
    return None


def list_tools():
    """List all available tools."""
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "python-client", "version": "1.0"}
        }
    }
    
    list_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    input_data = json.dumps(init_msg) + "\n" + json.dumps(list_msg)
    
    try:
        result = subprocess.run(
            ["python3", str(SERVER_PATH)],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if line.startswith('{"jsonrpc'):
                try:
                    response = json.loads(line)
                    if response.get('id') == 2:
                        tools = response.get('result', {}).get('tools', [])
                        return tools
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error listing tools: {e}", file=sys.stderr)
    
    return []


def print_usage():
    """Print usage information."""
    print("Falcon IQ Manager MCP Client")
    print("=" * 60)
    print()
    print("Usage:")
    print("  python mcp_client.py <tool_name> [arguments_json]")
    print("  python mcp_client.py --list")
    print()
    print("Examples:")
    print("  python mcp_client.py list_all_users")
    print("  python mcp_client.py search_okrs '{\"search_term\": \"resiliency\"}'")
    print("  python mcp_client.py get_pr_details '{\"pr_id\": 12345}'")
    print("  python mcp_client.py query_review_comments '{\"group_by\": \"signal\"}'")
    print()
    print("Options:")
    print("  --list    List all available tools")
    print("  --help    Show this help message")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Handle special commands
    if command in ["--help", "-h"]:
        print_usage()
        sys.exit(0)
    
    if command in ["--list", "-l"]:
        print("Available tools:")
        print("-" * 60)
        tools = list_tools()
        for tool in tools:
            name = tool.get('name', 'unknown')
            desc = tool.get('description', 'No description')
            # Truncate long descriptions
            if len(desc) > 80:
                desc = desc[:77] + "..."
            print(f"  {name:25} {desc}")
        sys.exit(0)
    
    # Parse arguments
    tool_name = command
    arguments = {}
    
    if len(sys.argv) >= 3:
        try:
            arguments = json.loads(sys.argv[2])
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON arguments: {e}", file=sys.stderr)
            print("Arguments must be valid JSON, e.g., '{\"pr_id\": 12345}'", file=sys.stderr)
            sys.exit(1)
    
    # Call the tool
    result = call_mcp_tool(tool_name, arguments)
    
    if result is None:
        print("Error: No result returned", file=sys.stderr)
        sys.exit(1)
    
    # Pretty print the result
    content = result.get('content', [])
    if content:
        for item in content:
            if item.get('type') == 'text':
                text = item.get('text', '')
                try:
                    # Try to parse and pretty-print JSON
                    data = json.loads(text)
                    print(json.dumps(data, indent=2))
                except json.JSONDecodeError:
                    # Not JSON, print as-is
                    print(text)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
