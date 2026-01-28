# Falcon Python Backend

A Python-based pipeline for downloading and processing GitHub Pull Request data.

## Overview

This project provides a complete pipeline to:
1. Generate PR tasks for users based on date ranges
2. Search and download PR lists from GitHub
3. Download detailed PR information (metadata, comments, files)
4. Parse and structure OKR files for users
5. Map OKRs to PRs with intelligent AI-powered classification
6. Extract and organize PR comments
7. Classify PR comments using OpenAI into feedback categories

## Features

- ✅ Automated task generation with incremental updates
- ✅ GitHub API integration with rate limiting and retry logic
- ✅ Batch processing for large datasets (10 PRs at a time)
- ✅ Progress tracking with status files
- ✅ Configurable base directory support
- ✅ Case-insensitive command-line arguments
- ✅ OKR parsing and intelligent PR-to-OKR mapping with AI
- ✅ PR comment extraction (authored/reviewed split)
- ✅ AI-powered comment classification (17 feedback categories)
- ✅ Cost tracking for OpenAI API usage
- ✅ Single batch mode for incremental processing

## Requirements

- Python 3.10 or higher
- GitHub Personal Access Token

## Installation

### 1. Clone/Navigate to the Project
```bash
cd falcon-python-backend
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration Setup

Create the required directory structure:
```bash
mkdir -p <base_dir>/{tasks,pr_data,settings,user_data}
```

#### Configure `pipeline_config.json`
```json
{
  "base_dir": "/path/to/your/data",
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

#### Create `settings/user-settings.json`
```json
{
  "organization": "your-github-org",
  "github_token": "ghp_your_token_here",
  "start_date": "2025-11-01",
  "openai_api_key": "sk-your-openai-key-here",
  "comment_classification_batch_size": 50,
  "comment_classification_single_batch_mode": false,
  "ai_reviewer_prefixes": ["github-actions", "svc-gha"]
}
```

#### Create `user_data/users.json`
```json
[
  {
    "firstName": "John",
    "lastName": "Doe",
    "userName": "jdoe",
    "prUserName": "jdoe_GitHubOrg"
  }
]
```

## Usage

### Quick Start
```bash
# Run full pipeline
python runPipeline.py

# Use custom base directory
python runPipeline.py --base-dir /path/to/data

# Start from specific step
python runPipeline.py --start-from 2

# Run specific steps only
python runPipeline.py --steps 2,3
```

### Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--base-dir PATH` | Override base directory | `--base_dir /custom/path` |
| `--start-from N` | Start from step N (1-3) | `--start-from 2` |
| `--steps X,Y,Z` | Run specific steps | `--steps 1,3` |
| `--list` | List available steps | `--list` |
| `-h, --help` | Show help | `-h` |

**Note:** The `--base-dir` argument is case-insensitive and accepts both hyphen and underscore:
- `--base-dir`, `--base_dir`, `--BASE-DIR`, `--BASE_DIR`, etc.

### Pipeline Steps

1. **Task Generation** (`prTaskGenerator.py`)
   - Generates PR tasks for each user
   - Manages incremental updates
   - Creates status files for tracking

2. **PR Search** (`prSearchTaskExecutor.py`)
   - Downloads PR lists from GitHub
   - Saves results as CSV files
   - Updates status to `pr-search-file-downloaded`

3. **PR Details Download** (`prDownloadExecutor.py`)
   - Downloads full PR details (metadata, comments, files)
   - Processes in batches of 10 PRs
   - Updates status to `pr-details-downloaded`

4. **OKR Parsing** (`okrParser.py`)
   - Parses raw OKR files for each user
   - Structures OKRs with objectives and key results
   - Outputs to `okrs/parsed/`

5. **OKR Mapping** (`prOKRMapper.py`)
   - Maps OKRs to PRs using AI embeddings
   - Intelligent classification with fallback categories
   - Tracks OpenAI API costs
   - Creates `okrs_{username}.csv`

6. **Comment Generation** (`prCommentFileGenerator.py`)
   - Extracts PR comments for each user
   - Creates two files: authored PRs and reviewed PRs
   - Configurable username mapping

7. **Comment Classification** (`prCommentClassification.py`)
   - Classifies comments into 17 feedback categories
   - Uses OpenAI GPT-4o-mini for human comments
   - Skips AI for bot comments (no cost)
   - Batch processing with status tracking

## Project Structure

```
falcon-python-backend/
├── common.py                      # Common utilities and config loading
├── githubCommonFunctions.py       # GitHub API interaction functions
├── prTaskGenerator.py             # Task generation script
├── prSearchTaskExecutor.py        # PR search and download script
├── prDownloadExecutor.py          # PR details download script
├── okrParser.py                   # OKR parsing script
├── prOKRMapper.py                 # OKR-to-PR mapping script
├── prCommentFileGenerator.py      # Comment extraction script
├── prCommentClassification.py     # Comment classification script
├── runPipeline.py                 # Main pipeline orchestrator
├── pipeline_config.json           # Pipeline configuration
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── README_PIPELINE.md             # Detailed pipeline guide
└── BASE_DIR_FEATURE.md            # Technical documentation
```

## Data Structure

```
<base_dir>/
├── tasks/                         # Task and status files
│   ├── pr_authored_user1.json
│   ├── pr_authored_user1_status.json
│   ├── pr_reviewer_user1.json
│   ├── pr_reviewer_user1_status.json
│   ├── user1_comments_classification_authored_status.json
│   └── user1_comments_classification_reviewed_status.json
├── pr_data/
│   ├── search/                    # PR list CSV files
│   │   └── pr_authored_user1_2025-11-01_2026-01-26.csv
│   ├── comments/                  # Extracted comment files
│   │   ├── user1_comments_on_authored_prs_2025-11-01_2026-01-26.csv
│   │   └── user1_comments_on_reviewed_prs_2025-11-01_2026-01-26.csv
│   └── {owner}/                   # Detailed PR data by repo
│       └── {repo}/
│           └── pr_{number}/
│               ├── pr_{number}_meta.csv
│               ├── pr_{number}_comments.csv
│               └── pr_{number}_files.csv
├── okrs/
│   ├── input/                     # Raw OKR files (user provided)
│   │   └── user1_okrs.csv
│   ├── parsed/                    # Parsed OKR files
│   │   └── user1_okrs_parsed.csv
│   └── okrs_user1.csv            # OKRs mapped to PRs
├── settings/
│   └── user-settings.json         # GitHub token, org, dates, OpenAI key
└── user_data/
    └── users.json                 # User information
```

## Status Files

Each task has a corresponding status file that tracks progress:

```json
{
  "status": "pr-details-downloaded",
  "current_row": 32
}
```

**Status Values:**
- `not_started` - Task created but no work done
- `in_progress` - Task currently being processed
- `pr-search-file-downloaded` - PR list downloaded from GitHub
- `pr-details-downloaded` - All PR details downloaded
- `completed` - Task fully processed

## Examples

### Development Workflow
```bash
# Set up test environment
python runPipeline.py --base-dir ~/test-data

# Run only task generation
python runPipeline.py --steps 1

# Run search and download
python runPipeline.py --steps 2,3
```

### Production Workflow
```bash
# Full pipeline with production data
python runPipeline.py --base-dir /mnt/production

# Resume interrupted download
python runPipeline.py --base-dir /mnt/production --start-from 3
```

### Multiple Environments
```bash
# Production
python runPipeline.py --base_dir /mnt/production

# Staging
python runPipeline.py --base_dir /mnt/staging

# Development
python runPipeline.py --base_dir ~/local-dev
```

## Features in Detail

### Global Base Directory Override
The pipeline supports runtime base directory override via command-line argument. This allows you to:
- Run pipeline on different datasets without config changes
- Test with separate data directories
- Support multiple environments (dev/staging/production)

See [BASE_DIR_FEATURE.md](BASE_DIR_FEATURE.md) for technical details.

### Batch Processing
PR details are downloaded in batches of 10 to:
- Prevent timeouts on large datasets
- Allow incremental progress
- Enable pause/resume functionality

### Rate Limiting
GitHub API calls include automatic rate limiting:
- Checks `X-RateLimit-Remaining` header
- Waits until `X-RateLimit-Reset` when limit reached
- Implements exponential backoff for errors

### Idempotency
The pipeline is designed to be safely re-run:
- Skips already downloaded PRs
- Resumes from last processed row
- Updates status files incrementally

## Troubleshooting

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### SSL Certificate Issues
```bash
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### GitHub Rate Limiting
- The pipeline automatically handles rate limits
- Wait time is displayed when limit is reached
- Consider using a GitHub App token for higher limits

### Pipeline Timeout
- Increase timeout in `pipeline_config.json`:
  ```json
  "timeout_per_step_seconds": 1800
  ```
- Use batch processing (Step 3 downloads 10 PRs at a time)

## Documentation

- [README_PIPELINE.md](README_PIPELINE.md) - Comprehensive pipeline guide
- [BASE_DIR_FEATURE.md](BASE_DIR_FEATURE.md) - Base directory override feature
- Run `python runPipeline.py --help` for command-line options

## Development

### Running Individual Scripts
Each script can be run independently:
```bash
python prTaskGenerator.py
python prSearchTaskExecutor.py
python prDownloadExecutor.py
```

### Testing
```bash
# Test with small dataset
python runPipeline.py --base-dir /tmp/test-data --steps 1,2
```

## License

Internal project - LinkedIn

## Contributing

For questions or issues, contact the project maintainers.
