#!/bin/bash
# Test script for Manager MCP Server
# Usage: ./test-server.sh

set -e

echo "Testing Falcon IQ Manager MCP Server..."
echo "========================================"
echo ""

# Check if environment variables are set
if [ -z "$FALCON_BASE_DIR" ]; then
    echo "Warning: FALCON_BASE_DIR not set"
    echo "Set it with: export FALCON_BASE_DIR=/path/to/base/dir"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY not set (required for AI features)"
fi

echo ""
echo "Test 1: Initialize and list available tools"
echo "--------------------------------------------"
cat << 'EOFINPUT' | python3 manager-mcp-server.py 2>&1 | grep -E "(tools|name|description)" | head -30
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOFINPUT

echo ""
echo "Test 2: Count available tools"
echo "------------------------------"
cat << 'EOFINPUT' | python3 manager-mcp-server.py 2>&1 | grep -o '"name":"[^"]*"' | wc -l
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOFINPUT

echo ""
echo "Test 3: Verify tool names"
echo "-------------------------"
cat << 'EOFINPUT' | python3 manager-mcp-server.py 2>&1 | grep -o '"name":"[^"]*"' | sort | uniq
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
EOFINPUT

echo ""
echo "========================================"
echo "Testing complete!"
echo ""
echo "To add this server to Cursor:"
echo "1. Copy example-mcp-config.json content"
echo "2. Add to ~/.cursor/config/mcp.json"
echo "3. Update paths and environment variables"
echo "4. Restart Cursor"
