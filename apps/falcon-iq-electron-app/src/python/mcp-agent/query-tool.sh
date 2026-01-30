#!/bin/bash
# Quick helper script to query MCP tools from command line
# Usage: ./query-tool.sh <tool_name> <arguments_json>

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <tool_name> [arguments_json]"
    echo ""
    echo "Examples:"
    echo "  $0 list_all_users"
    echo "  $0 search_okrs '{\"search_term\": \"resiliency\"}'"
    echo "  $0 get_pr_details '{\"pr_id\": 12345}'"
    echo "  $0 query_review_comments '{\"group_by\": \"signal\", \"limit\": 10}'"
    echo ""
    echo "Available tools:"
    echo "  - get_pr_details"
    echo "  - get_comment_details"
    echo "  - get_pr_files"
    echo "  - search_okrs"
    echo "  - list_all_okrs"
    echo "  - generate_okr_update"
    echo "  - query_pr_stats"
    echo "  - find_prs_by_okr"
    echo "  - list_all_users"
    echo "  - query_users"
    echo "  - query_review_comments"
    exit 1
fi

TOOL_NAME="$1"
ARGUMENTS="${2:-{}}"

# Create the MCP protocol messages
cat << EOF | python3 "$SCRIPT_DIR/manager-mcp-server.py" 2>&1 | grep '^{' | tail -1 | python3 -m json.tool 2>/dev/null || cat
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "cli", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "$TOOL_NAME", "arguments": $ARGUMENTS}}
EOF
