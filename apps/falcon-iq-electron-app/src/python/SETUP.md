# Falcon Python Backend - Setup Guide

Complete setup instructions for the PR data pipeline.

## Prerequisites

- **Python**: 3.10 or higher (tested with 3.13)
- **Git**: For cloning the repository (optional)
- **GitHub Token**: Personal Access Token with `repo` scope

## Quick Setup (5 minutes)

### 1. Install Python Dependencies

```bash
cd falcon-python-backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Create Directory Structure

```bash
# Choose your base directory (example: ~/falcon-data)
BASE_DIR=~/falcon-data

# Create required folders
mkdir -p $BASE_DIR/{tasks,pr_data,pr_data/search,settings,user_data}
```

### 3. Configure Pipeline

Create `pipeline_config.json`:
```json
{
  "base_dir": "/Users/your-username/falcon-data",
  "okr_folder": "okrs",
  "output_folder": "output",
  "pr_data_folder": "pr_data",
  "user_data_folder": "user_data",
  "settings_folder": "settings",
  "task_folder": "tasks",
  "pipeline": {
    "default_start_step": 1,
    "timeout_per_step_seconds": 1200,
    "continue_on_error": false
  }
}
```

### 4. Add User Settings

Create `$BASE_DIR/settings/user-settings.json`:
```json
{
  "organization": "your-github-org",
  "github_token": "ghp_your_github_token_here",
  "start_date": "2025-11-01"
}
```

**To get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scope: `repo` (Full control of private repositories)
4. Copy the token and paste it in the config

### 5. Add Users

Create `$BASE_DIR/user_data/users.json`:
```json
[
  {
    "firstName": "John",
    "lastName": "Doe",
    "userName": "jdoe",
    "prUserName": "jdoe_GitHubOrg"
  },
  {
    "firstName": "Jane",
    "lastName": "Smith",
    "userName": "jsmith",
    "prUserName": "jsmith_GitHubOrg"
  }
]
```

**Field explanations:**
- `firstName`, `lastName`: User's name
- `userName`: Internal identifier (used for file naming)
- `prUserName`: GitHub username (format: `username_organization`)

### 6. Test Installation

```bash
# List available pipeline steps
python runPipeline.py --list

# Test with help
python runPipeline.py --help
```

## Detailed Setup

### Python Environment Setup

#### Option 1: Using venv (Recommended)
```bash
# Create virtual environment
python3 -m venv .venv

# Activate
source .venv/bin/activate

# Install
pip install -r requirements.txt
```

#### Option 2: Using conda
```bash
# Create conda environment
conda create -n falcon python=3.13

# Activate
conda activate falcon

# Install
pip install -r requirements.txt
```

#### Option 3: System Python (Not recommended)
```bash
# Install globally
pip install -r requirements.txt
```

### SSL Certificate Issues

If you encounter SSL errors during pip install:
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### Verifying Installation

```bash
# Check Python version
python --version  # Should be 3.10+

# Check installed packages
pip list | grep -E "pandas|requests"

# Expected output:
# pandas      3.0.0
# requests    2.32.5

# Verify no broken dependencies
pip check

# Test imports
python -c "import pandas; import requests; print('✅ All imports successful')"
```

## Configuration Files

### 1. pipeline_config.json (Project Root)

Location: `falcon-python-backend/pipeline_config.json`

```json
{
  "base_dir": "/absolute/path/to/data/folder",
  "okr_folder": "okrs",
  "output_folder": "output",
  "pr_data_folder": "pr_data",
  "user_data_folder": "user_data",
  "settings_folder": "settings",
  "task_folder": "tasks",
  "pipeline": {
    "default_start_step": 1,
    "timeout_per_step_seconds": 1200,
    "continue_on_error": false
  }
}
```

**Important:**
- Use absolute paths for `base_dir`
- Expand `~` to full path: `/Users/your-username/`
- Ensure the directory exists or will be created

### 2. user-settings.json (Data Folder)

Location: `$BASE_DIR/settings/user-settings.json`

```json
{
  "organization": "your-github-org",
  "github_token": "ghp_your_token_here",
  "start_date": "2025-11-01"
}
```

**Fields:**
- `organization`: GitHub organization name
- `github_token`: GitHub Personal Access Token
- `start_date`: Starting date for PR search (YYYY-MM-DD)

### 3. users.json (Data Folder)

Location: `$BASE_DIR/user_data/users.json`

```json
[
  {
    "firstName": "First",
    "lastName": "Last",
    "userName": "username",
    "prUserName": "github_username_org"
  }
]
```

**Multiple users example:**
```json
[
  {
    "firstName": "John",
    "lastName": "Doe",
    "userName": "jdoe",
    "prUserName": "jdoe_LinkedIn"
  },
  {
    "firstName": "Jane",
    "lastName": "Smith",
    "userName": "jsmith",
    "prUserName": "jsmith_LinkedIn"
  }
]
```

## Directory Structure After Setup

```
.
├── falcon-python-backend/           # Project code
│   ├── common.py
│   ├── githubCommonFunctions.py
│   ├── prTaskGenerator.py
│   ├── prSearchTaskExecutor.py
│   ├── prDownloadExecutor.py
│   ├── runPipeline.py
│   ├── pipeline_config.json         # Main config
│   ├── requirements.txt
│   ├── README.md
│   └── .venv/                       # Virtual environment
│
└── falcon-data/                     # Data folder (can be anywhere)
    ├── tasks/                       # Generated by pipeline
    ├── pr_data/
    │   └── search/                  # Generated by pipeline
    ├── settings/
    │   └── user-settings.json       # Create this
    └── user_data/
        └── users.json               # Create this
```

## First Run

### Test the Pipeline

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. List available steps
python runPipeline.py --list

# 3. Run task generation only (safe test)
python runPipeline.py --steps 1

# 4. If successful, run full pipeline
python runPipeline.py
```

### Expected Output

```
================================================================================
🚀 PR DATA PIPELINE RUNNER
================================================================================
📁 Using base directory from pipeline_config.json

📋 Pipeline Configuration:
   Running specific steps: 1, 2, 3
   Total steps: 3

📍 STEP 1/3: Task Generation
   ...
✅ Step 1 completed successfully

📍 STEP 2/3: PR Search
   ...
✅ Step 2 completed successfully

📍 STEP 3/3: PR Details Download
   ...
✅ Step 3 completed successfully

🎉 Pipeline completed successfully!
```

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Configuration Not Found

**Problem:** `FileNotFoundError: Config file not found`

**Solution:**
```bash
# Ensure you're in the project directory
cd falcon-python-backend

# Check if pipeline_config.json exists
ls -l pipeline_config.json
```

### GitHub API Errors

**Problem:** `401 Unauthorized` or `403 Forbidden`

**Solution:**
- Verify GitHub token is correct in `user-settings.json`
- Check token has `repo` scope
- Token format: `ghp_...` (starts with ghp_)

### Directory Not Found

**Problem:** `FileNotFoundError: User settings file not found`

**Solution:**
```bash
# Create missing directories
BASE_DIR=~/falcon-data
mkdir -p $BASE_DIR/{settings,user_data}

# Create the config files
# ... follow steps 4 and 5 above
```

### Rate Limiting

**Problem:** `GitHub API rate limit exceeded`

**Solution:**
- Wait for rate limit reset (displayed in error)
- Pipeline automatically waits and retries
- For higher limits, use GitHub App token

## Updating Dependencies

```bash
# Activate environment
source .venv/bin/activate

# Update to latest versions
pip install --upgrade requests pandas

# Or use specific versions
pip install requests==2.32.5 pandas==3.0.0

# Regenerate requirements
pip freeze > requirements-freeze.txt
```

## Upgrading Python Version

```bash
# Remove old virtual environment
rm -rf .venv

# Create new with desired Python version
python3.13 -m venv .venv

# Activate and reinstall
source .venv/bin/activate
pip install -r requirements.txt
```

## Running on Different Machines

### Export Configuration
```bash
# On source machine
cd falcon-python-backend
pip freeze > requirements-exact.txt
```

### Import on New Machine
```bash
# On target machine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-exact.txt
```

## Docker Setup (Optional)

If you prefer to use Docker:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "runPipeline.py"]
```

```bash
# Build
docker build -t falcon-backend .

# Run
docker run -v /path/to/data:/data falcon-backend --base-dir /data
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review README.md and README_PIPELINE.md
3. Contact project maintainers

## Next Steps

After setup:
1. ✅ Read [README.md](README.md) for usage overview
2. ✅ Read [README_PIPELINE.md](README_PIPELINE.md) for detailed guide
3. ✅ Run your first pipeline with `python runPipeline.py`
4. ✅ Review generated data in `$BASE_DIR/pr_data/`
