# Smart Agent API Documentation

The Smart Agent is now integrated into the FastAPI server and available as HTTP endpoints.

## Endpoints

### 1. Get Agent Capabilities
**GET** `/api/smart-agent/capabilities`

Returns information about what the smart agent can do and example queries.

**Example:**
```bash
curl http://127.0.0.1:8765/api/smart-agent/capabilities
```

**Response:**
```json
{
  "success": true,
  "capabilities": [
    {
      "name": "PR Analysis",
      "description": "Get detailed information about specific PRs",
      "examples": [
        "Show me PR 1013",
        "Get details about pull request 660"
      ]
    },
    ...
  ],
  "tools": [
    "get_pr_details",
    "get_comment_details",
    "get_pr_files",
    "list_all_users",
    ...
  ]
}
```

---

### 2. Query the Smart Agent
**POST** `/api/smart-agent/query`

Send natural language queries to the smart agent.

**Request Body:**
```json
{
  "query": "Your natural language question here"
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:8765/api/smart-agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all users in the system"}'
```

**Response:**
```json
{
  "success": true,
  "query": "List all users in the system",
  "answer": "### List of Users in the System\n\nHere is a comprehensive list..."
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message",
  "traceback": "Detailed traceback if available"
}
```

---

## Available Capabilities

### 1. **PR Analysis**
Get detailed information about specific PRs.

**Example Queries:**
- "Show me PR 1013"
- "Get details about pull request 660"
- "What files were changed in PR 1013?"

### 2. **User Management**
Query and list users in the system.

**Example Queries:**
- "List all users"
- "Who are the users in the system?"
- "Show me all users with their email addresses"

### 3. **OKR Tracking**
Search for OKRs and generate updates.

**Example Queries:**
- "Search for Reserved Ads OKR"
- "What OKRs are in the system?"
- "Show me all OKRs for Q1 2026"

### 4. **Code Review Analytics**
Analyze code review comments with signal classifications.

**Example Queries:**
- "Show me all performance-related comments"
- "How many bug comments did I make?"
- "What's my comment breakdown by category?"
- "Show me security-related review comments"

### 5. **PR Statistics**
Query PR statistics and review data.

**Example Queries:**
- "How many PRs did I review for John?"
- "Show me authors where I left more than 10 comments"
- "What's my average comments per PR?"

### 6. **OKR Update Generation**
Generate AI-powered technical and executive updates for OKRs.

**Example Queries:**
- "Write me an update for Reserved Ads goal for Jan 2026"
- "Generate executive summary for the ML OKR"
- "Create a technical update for the performance optimization goal"

---

## How It Works

1. **Query Planning**: The agent analyzes your natural language query and creates a plan
2. **Tool Execution**: It executes the necessary tools (database queries, file reads, etc.)
3. **Result Synthesis**: It synthesizes all the information into a comprehensive answer using GPT-4o

---

## Configuration

The smart agent uses:
- **Database**: SQLite database from `FALCON_BASE_DIR`
- **OpenAI API**: Key loaded from `settings.json` or `OPENAI_API_KEY` environment variable
- **Base Directory**: Configured via `FALCON_BASE_DIR` environment variable

---

## Integration Examples

### JavaScript/TypeScript (Electron Renderer)
```typescript
async function querySmartAgent(query: string) {
  const response = await fetch('http://127.0.0.1:8765/api/smart-agent/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  
  const data = await response.json();
  
  if (data.success) {
    console.log('Answer:', data.answer);
  } else {
    console.error('Error:', data.error);
  }
}

// Usage
await querySmartAgent('List all users in the system');
await querySmartAgent('Generate update for Reserved Ads goal for Jan 2026');
```

### Python
```python
import requests

def query_smart_agent(query: str):
    response = requests.post(
        'http://127.0.0.1:8765/api/smart-agent/query',
        json={'query': query}
    )
    data = response.json()
    
    if data['success']:
        print(f"Answer: {data['answer']}")
    else:
        print(f"Error: {data['error']}")

# Usage
query_smart_agent('List all users in the system')
query_smart_agent('Generate update for Reserved Ads goal for Jan 2026')
```

### curl (Command Line)
```bash
# Simple query
curl -X POST http://127.0.0.1:8765/api/smart-agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all users"}'

# Complex query
curl -X POST http://127.0.0.1:8765/api/smart-agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Write me an update for Reserved Ads goal for Jan 2026 by looking at all the PRs and generating an update using its body"}'
```

---

## Performance Notes

- **First Query**: The first query may take longer (15-30 seconds) as the agent initializes
- **Subsequent Queries**: Faster as the agent instance is cached
- **Complex Queries**: Queries requiring multiple tools or AI generation may take 30-60 seconds
- **Async Execution**: The endpoint uses async execution to prevent blocking the server

---

## Error Handling

The agent will return detailed error information if something goes wrong:

```json
{
  "success": false,
  "error": "No OKRs found matching: NonExistentOKR",
  "traceback": "..."
}
```

Common errors:
- **Empty Query**: "Query cannot be empty"
- **Database Error**: "Database not found" or "No such table"
- **API Key Missing**: "OpenAI API key not found"
- **Tool Error**: Specific error from the tool that failed

---

## Testing

```bash
# 1. Start the server
cd /Users/npurwar/Documents/GitHub/tiberius/apps/falcon-iq-electron-app/src/python
export FALCON_BASE_DIR="/Users/npurwar/Library/Application Support/Falcon IQ"
python3 server.py 8765 "$FALCON_BASE_DIR" false

# 2. Test health check
curl http://127.0.0.1:8765/health

# 3. Test capabilities
curl http://127.0.0.1:8765/api/smart-agent/capabilities

# 4. Test simple query
curl -X POST http://127.0.0.1:8765/api/smart-agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all users"}'

# 5. Test complex query
curl -X POST http://127.0.0.1:8765/api/smart-agent/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Generate update for Reserved Ads goal for Jan 2026"}'
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server (server.py)               │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         /api/smart-agent/query (POST)                 │ │
│  │                                                         │ │
│  │  1. Receive natural language query                    │ │
│  │  2. Run SmartAgent in ThreadPoolExecutor (async)      │ │
│  │  3. Return structured response                        │ │
│  └───────────────────────────────────────────────────────┘ │
│                              ↓                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              SmartAgent (smart-agent.py)              │ │
│  │                                                         │ │
│  │  • Planner Node: Analyze query, create plan          │ │
│  │  • Executor Node: Execute tools                       │ │
│  │  • Synthesizer Node: Generate final answer           │ │
│  └───────────────────────────────────────────────────────┘ │
│                              ↓                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                   MCP Tools                            │ │
│  │                                                         │ │
│  │  • get_pr_details        • search_okrs                │ │
│  │  • get_comment_details   • list_all_okrs              │ │
│  │  • get_pr_files          • find_prs_by_okr            │ │
│  │  • list_all_users        • generate_okr_update        │ │
│  │  • query_users           • query_review_comments      │ │
│  │  • query_pr_stats                                     │ │
│  └───────────────────────────────────────────────────────┘ │
│                              ↓                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │         SQLite Database + Filesystem                  │ │
│  │                                                         │ │
│  │  • pr_stats table                                     │ │
│  │  • pr_comment_details table                           │ │
│  │  • goals table (OKRs)                                 │ │
│  │  • PR bodies/files on disk                            │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Next Steps

1. **Frontend Integration**: Add a UI component in the Electron app to interact with the agent
2. **Streaming Responses**: Implement server-sent events for real-time progress updates
3. **Query History**: Store and retrieve previous queries
4. **Agent Customization**: Allow users to customize agent behavior
5. **Multi-turn Conversations**: Support follow-up questions and context
