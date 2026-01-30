# PR Analytics Agent 🤖

A LangGraph-based intelligent agent that answers natural language questions about your GitHub PR data by generating and executing safe, read-only SQL queries against a local SQLite database.

## Features

✅ **Natural Language Interface** - Ask questions in plain English  
✅ **Safe SQL Generation** - LLM generates SQL from your questions  
✅ **Multi-Layer Validation** - Hard gates prevent dangerous queries  
✅ **Intelligent Retry** - Automatically fixes SQL validation errors  
✅ **Interactive & CLI Modes** - Use interactively or as a command  
✅ **Database Diagnostics** - Built-in health check tools  

## Quick Start

### 1. Install Dependencies

```bash
cd apps/falcon-iq-electron-app/src/python
pip install -r requirements.txt
```

### 2. Configure Settings

The agent automatically reads configuration from your existing settings file:
- **Development**: `~/Library/Application Support/Falcon IQ/settings.dev.json`
- **Production**: `~/Library/Application Support/Falcon IQ/settings.json`

The settings file should contain:
```json
{
  "openai_api_key": "sk-your-key-here",
  "integrations": {
    "github": {
      "username": "your-username"
    }
  }
}
```

**Optional Environment Variables** (override settings file):
```bash
# Override OpenAI API key
export OPENAI_API_KEY="your-key-here"

# Override username
export FALCON_USERNAME="your-username"

# Override base directory
export FALCON_BASE_DIR="/custom/path"
export FALCON_IS_DEV="1"  # Use database.dev.db
```

### 3. Verify Database Connection

Run the database doctor to ensure everything is set up correctly:

```bash
python -m app.main --doctor
```

Expected output:
```
================================================================================
DATABASE DIAGNOSTICS
================================================================================

✅ Database file found: /Users/you/Library/Application Support/Falcon IQ/database.dev.db
   Size: 2.45 MB

✅ Connection successful
   Tables found: 4

Table Summary:
--------------------------------------------------------------------------------
  ✅ users: 10 rows
  ✅ goals: 25 rows
  ✅ pr_stats: 150 rows
  ✅ pr_comment_details: 1,234 rows

Total rows across all tables: 1,419

✅ Database is healthy and ready!
```

### 4. Ask Questions!

**One-off questions:**
```bash
python -m app.main "What are my top PRs?"

# With custom base directory
python -m app.main --base-dir ~/Library/Application\ Support/Falcon\ IQ "What are my top PRs?"
```

**Interactive mode:**
```bash
python -m app.main

# With custom base directory
python -m app.main --base-dir ~/Library/Application\ Support/Falcon\ IQ
```

## Usage Examples

### Example Questions

```bash
# Top PRs by comment activity
python -m app.main "What are my top PRs?"

# User who received most comments from you
python -m app.main "Which user did I give the most comments on?"

# Top 5 users by comments received
python -m app.main "Which user did I give the most comments on (top 5)?"

# User who gave you most comments
python -m app.main "Which user gave me the most comments?"

# PRs where you commented on reliability
python -m app.main "Show PRs where I gave comments on resiliency/reliability"

# OKR updates in timeframe
python -m app.main "Tell me the update for Phoenix OKR in the last 3 weeks"

# Custom username
python -m app.main --username alice "What are my top PRs?"
```

### Interactive Mode

```bash
$ python -m app.main

================================================================================
PR Analytics Agent - Interactive Mode
================================================================================

Current user: npurwar
Database: /Users/npurwar/Library/Application Support/Falcon IQ/database.dev.db

Commands:
  - Type your question and press Enter
  - Type 'doctor' to run diagnostics
  - Type 'schema' to see database schema
  - Type 'quit' or 'exit' to exit

❓ Ask a question: What are my top PRs?

🔍 Parsing question...
   Entities: {'username': 'npurwar', 'intent': 'top_prs'}
⚙️  Generating SQL...
   Generated SQL:
   SELECT pr_number, repo, total_comments, task_type
   FROM pr_stats
   WHERE username = 'npurwar'
   ORDER BY total_comments DESC
   LIMIT 10
✅ Validating SQL...
   ✅ SQL is valid and safe
🔄 Executing SQL...
   ✅ Query returned 10 rows
📊 Summarizing results...
   ✅ Summary generated

================================================================================
RESULTS
================================================================================

SQL Query:
```sql
SELECT pr_number, repo, total_comments, task_type
FROM pr_stats
WHERE username = 'npurwar'
ORDER BY total_comments DESC
LIMIT 10
```

Data (10 rows):

| pr_number | repo | total_comments | task_type |
|-----------|------|----------------|-----------|
| 12345 | my-repo | 45 | reviewed |
| 12346 | my-repo | 38 | authored |
...

Summary:
Your top PRs by comment activity are...
[LLM-generated summary with insights and follow-up suggestions]

================================================================================

❓ Ask a question: 
```

## Architecture

### LangGraph Workflow

The agent uses a multi-node graph to process questions:

```
┌──────────────┐
│Parse Question│  ← Extract entities & intent
└──────┬───────┘
       │
       v
┌──────────────┐
│Generate SQL  │  ← LLM generates SQL query
└──────┬───────┘
       │
       v
┌──────────────┐
│Validate SQL  │  ← Hard safety gate
└──────┬───────┘
       │
       v
    ┌──┴──┐
    │Valid?│
    └──┬──┘
       │
  ┌────┴────┐
 No│        │Yes
   v         v
┌─────┐  ┌─────────┐
│Retry│  │Run SQL  │  ← Execute query
│(3x) │  └────┬────┘
└─────┘       │
              v
         ┌─────────┐
         │Summarize│  ← LLM summarizes
         └─────────┘
```

### Safety Features

**SQL Validation Rules:**
1. ✅ Must start with `SELECT` (read-only)
2. ✅ Must include `LIMIT` clause (max 200)
3. ❌ No dangerous keywords (INSERT, UPDATE, DELETE, DROP, PRAGMA, etc.)
4. ❌ No multiple statements (semicolons)
5. ❌ No SQL comments or escape sequences
6. ✅ Automatic retry with error feedback (up to 3 attempts)

### File Structure

```
app/
├── __init__.py          # Package init
├── main.py              # CLI entry point
├── graph.py             # LangGraph workflow
├── tools_sqlite.py      # Database tools
├── sql_guard.py         # SQL validator
├── prompts.py           # LLM prompts
└── config.py            # Configuration

tests/
├── __init__.py
├── test_sql_guard.py    # Validator tests
└── test_tools.py        # Database tools tests
```

## Database Schema

### Tables

**users**
- `id` (INTEGER PRIMARY KEY)
- `userName` (TEXT)
- `firstName` (TEXT)
- `lastName` (TEXT)
- `email` (TEXT)

**goals** (OKRs)
- `id` (INTEGER PRIMARY KEY)
- `userId` (INTEGER)
- `title` (TEXT)
- `description` (TEXT)
- `category` (TEXT)
- `status` (TEXT)
- `startDate` (TEXT)
- `endDate` (TEXT)
- `createdAt` (TEXT)

**pr_stats**
- `id` (INTEGER PRIMARY KEY)
- `username` (TEXT)
- `repo` (TEXT)
- `pr_number` (INTEGER)
- `task_type` (TEXT) - 'authored' or 'reviewed'
- `total_comments` (INTEGER)
- `comments_given` (INTEGER)
- `comments_received` (INTEGER)
- `start_date` (TEXT)
- `end_date` (TEXT)

**pr_comment_details**
- `id` (INTEGER PRIMARY KEY)
- `pr_number` (INTEGER)
- `comment_id` (INTEGER)
- `username` (TEXT) - Comment author
- `pr_author` (TEXT) - PR author
- `comment_type` (TEXT)
- `is_reviewer` (INTEGER) - 1 if commenter is reviewing
- `primary_category` (TEXT)
- `secondary_categories` (TEXT)
- `severity` (TEXT)
- `mentions_reliability` (INTEGER)
- `mentions_security` (INTEGER)
- `mentions_performance` (INTEGER)
- `mentions_testing` (INTEGER)
- ...more category flags

## CLI Reference

```bash
# Ask a question
python -m app.main "your question here"

# Interactive mode (omit question)
python -m app.main

# With custom base directory
python -m app.main --base-dir ~/Library/Application\ Support/Falcon\ IQ "your question"

# With custom username
python -m app.main --username alice "What are my top PRs?"

# With custom database path
python -m app.main --db /path/to/database.db "your question"

# Run database diagnostics
python -m app.main --doctor

# Run diagnostics with custom base directory
python -m app.main --base-dir ~/path/to/data --doctor

# Show database schema
python -m app.main --schema

# Hide SQL in output
python -m app.main --no-sql "your question"

# Setup verification
python -m app.verify_setup
python -m app.verify_setup --base-dir ~/Library/Application\ Support/Falcon\ IQ
```

## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_sql_guard.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Configuration

### Settings File

The agent reads configuration from your existing Falcon IQ settings file:
- **Development**: `~/Library/Application Support/Falcon IQ/settings.dev.json`
- **Production**: `~/Library/Application Support/Falcon IQ/settings.json`

Required fields in settings file:
```json
{
  "openai_api_key": "sk-your-openai-key",
  "integrations": {
    "github": {
      "username": "your-github-username",
      "pat": "ghp_your-github-token"
    }
  }
}
```

### Environment Variables (Optional Overrides)

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Override OpenAI API key from settings | From settings file |
| `FALCON_USERNAME` | Override username from settings | From settings file |
| `FALCON_BASE_DIR` | Override base directory | `~/Library/Application Support/Falcon IQ` |
| `FALCON_IS_DEV` | Use dev database (1/0) | `1` |

### Config File

Edit `app/config.py` to customize:
- `MAX_QUERY_LIMIT` - Maximum rows per query (default: 200)
- `DEFAULT_QUERY_LIMIT` - Default LIMIT value (default: 20)
- `OPENAI_MODEL` - LLM model (default: gpt-4o-mini)
- `DANGEROUS_KEYWORDS` - Blocked SQL keywords

## Troubleshooting

### Quick Verification

Run the setup verification script to check all configuration:
```bash
python -m app.verify_setup
```

This will check:
- Base directory and database location
- Settings file presence
- OpenAI API key configuration
- Default username

### Database not found

```bash
# Check database location
python -m app.main --doctor

# Override via command-line (recommended)
python -m app.main --base-dir ~/Library/Application\ Support/Falcon\ IQ --doctor

# Or override via environment variable
export FALCON_BASE_DIR=~/Library/Application\ Support/Falcon\ IQ
python -m app.main --doctor
```

### OpenAI API errors

```bash
# Check if API key is configured
python -c "from app.config import get_api_key; print('API key found!' if get_api_key() else 'No API key')"

# Verify settings file exists
ls -la ~/Library/Application\ Support/Falcon\ IQ/settings*.json

# Or set via environment variable
export OPENAI_API_KEY="sk-your-key-here"

# Test connection
python -c "from openai import OpenAI; print(OpenAI().models.list())"
```

### SQL validation fails repeatedly

The agent will retry up to 3 times with error feedback. If still failing:
1. Check if your question is too ambiguous
2. Try rephrasing more explicitly
3. Check database schema matches your question

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade

# Verify installation
python -c "import langgraph; print(langgraph.__version__)"
```

## Development

### Adding New Question Types

1. Add few-shot examples to `app/prompts.py`
2. Update `SYSTEM_PROMPT` with new patterns
3. Test with various phrasings

### Extending Validation

Add rules to `app/sql_guard.py`:
```python
def validate_sql(sql: str) -> Tuple[bool, Optional[str]]:
    # Add your validation logic
    if your_condition:
        return False, "Your error message"
    # ...
```

### Adding New Tools

Create functions in `app/tools_sqlite.py` and expose them in the graph.

## License

MIT License - See project root LICENSE file

## Support

For issues or questions:
- Check troubleshooting section
- Review test files for usage examples
- File an issue in the repository

---

Built with ❤️ using LangGraph, LangChain, and OpenAI
