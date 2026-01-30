# PR Analytics Agent - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd apps/falcon-iq-electron-app/src/python
pip install -r requirements.txt
```

### Step 2: Configure Settings (if not already done)

The agent uses your existing Falcon IQ settings file. Ensure it contains:
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

Location:
- Dev: `~/Library/Application Support/Falcon IQ/settings.dev.json`
- Prod: `~/Library/Application Support/Falcon IQ/settings.json`

Alternatively, set environment variable:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### Step 3: Verify Setup
```bash
# Quick verification of all configuration
python -m app.verify_setup

# Or specify base directory explicitly
python -m app.verify_setup --base-dir ~/Library/Application\ Support/Falcon\ IQ

# Or detailed database check
python -m app.main --doctor
```

Expected: ✅ Setup verification PASSED - Ready to use!

### Step 4: Ask Your First Question
```bash
python -m app.main "What are my top PRs?"
```

## 🎯 Common Questions

```bash
# Top PRs
python -m app.main "What are my top PRs?"

# Users I commented most on
python -m app.main "Which user did I give the most comments on (top 5)?"

# Users who commented on my PRs
python -m app.main "Which user gave me the most comments?"

# Reliability/resiliency comments
python -m app.main "Show PRs where I gave comments on resiliency"

# OKR updates
python -m app.main "Tell me about Phoenix OKR in the last 3 weeks"
```

## 💡 Interactive Mode

For a chat-like experience:
```bash
python -m app.main

# Then type questions and press Enter
❓ Ask a question: What are my top PRs?
❓ Ask a question: doctor
❓ Ask a question: schema
❓ Ask a question: quit
```

## 🔧 Troubleshooting

**Database not found?**
```bash
# Option 1: Use command-line flag (recommended)
python -m app.main --base-dir ~/Library/Application\ Support/Falcon\ IQ --doctor

# Option 2: Set environment variable
export FALCON_BASE_DIR=~/Library/Application\ Support/Falcon\ IQ
python -m app.main --doctor

# Option 3: Verify what path is being used
python -m app.verify_setup
```

**OpenAI error?**
```bash
# Verify API key
echo $OPENAI_API_KEY
```

**Import errors?**
```bash
# Reinstall
pip install -r requirements.txt --upgrade
```

## 📖 Full Documentation

See [README_AGENT.md](./README_AGENT.md) for complete documentation.

## 🧪 Run Tests

```bash
pytest tests/ -v
```

---

**Need help?** Check the full README or run `python -m app.main --help`
