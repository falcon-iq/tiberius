#!/bin/bash
# Automated setup script for Cursor MCP integration
# This script will create the MCP config file for you

set -e

echo "🚀 Falcon IQ Manager - Cursor MCP Setup"
echo "========================================"
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CURSOR_DIR="$HOME/Library/Application Support/Cursor/User"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CURSOR_DIR="$HOME/.config/Cursor/User"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    CURSOR_DIR="$APPDATA/Cursor/User"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

MCP_CONFIG="$CURSOR_DIR/mcp.json"

echo "📁 Cursor directory: $CURSOR_DIR"
echo "📄 MCP config file: $MCP_CONFIG"
echo ""

# Check if Cursor directory exists
if [ ! -d "$CURSOR_DIR" ]; then
    echo "❌ Cursor directory not found!"
    echo "   Please make sure Cursor is installed."
    exit 1
fi

# Get current directory (where this script is)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVER_PATH="$SCRIPT_DIR/manager-mcp-server.py"

# Ask for base directory
echo "🔧 Configuration Setup"
echo "----------------------"
echo ""
read -p "Enter your FALCON_BASE_DIR path: " BASE_DIR

# Validate base directory
if [ -z "$BASE_DIR" ]; then
    echo "❌ Base directory cannot be empty"
    exit 1
fi

# Expand ~ to home directory
BASE_DIR="${BASE_DIR/#\~/$HOME}"

# Ask for OpenAI API key (optional)
echo ""
read -p "Enter your OpenAI API key (optional, press Enter to skip): " API_KEY

# Create the config
echo ""
echo "📝 Creating MCP configuration..."

# Check if config already exists
if [ -f "$MCP_CONFIG" ]; then
    echo "⚠️  MCP config file already exists!"
    read -p "Do you want to backup and overwrite it? (y/n): " OVERWRITE
    if [[ "$OVERWRITE" != "y" && "$OVERWRITE" != "Y" ]]; then
        echo "❌ Setup cancelled"
        exit 0
    fi
    # Backup existing config
    cp "$MCP_CONFIG" "$MCP_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup created"
fi

# Create the config JSON
if [ -z "$API_KEY" ]; then
    # Without API key
    cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "falcon-iq-manager": {
      "command": "python3",
      "args": [
        "$SERVER_PATH"
      ],
      "env": {
        "FALCON_BASE_DIR": "$BASE_DIR"
      }
    }
  }
}
EOF
else
    # With API key
    cat > "$MCP_CONFIG" << EOF
{
  "mcpServers": {
    "falcon-iq-manager": {
      "command": "python3",
      "args": [
        "$SERVER_PATH"
      ],
      "env": {
        "FALCON_BASE_DIR": "$BASE_DIR",
        "OPENAI_API_KEY": "$API_KEY"
      }
    }
  }
}
EOF
fi

echo "✅ MCP configuration created successfully!"
echo ""
echo "📋 Configuration Summary"
echo "------------------------"
echo "Server path: $SERVER_PATH"
echo "Base directory: $BASE_DIR"
if [ -n "$API_KEY" ]; then
    echo "OpenAI API key: ***${API_KEY: -4}"
else
    echo "OpenAI API key: (not set)"
fi
echo ""
echo "🔄 Next Steps:"
echo "1. Restart Cursor completely"
echo "2. Open a new chat window"
echo "3. Type '@falcon-iq-manager' to see if it's available"
echo "4. Try a query like: '@falcon-iq-manager list all users'"
echo ""
echo "📚 For more information, see:"
echo "   - USAGE_GUIDE.md (comprehensive guide)"
echo "   - README.md (tool documentation)"
echo ""
echo "✨ Setup complete!"
