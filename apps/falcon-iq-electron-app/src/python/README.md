# Falcon Python Backend

A Python-based pipeline for downloading and processing GitHub Pull Request data.

## Overview

This project provides a complete pipeline to:
1. Generate PR tasks for users based on date ranges
2. Search and download PR lists from GitHub
3. Download detailed PR information (metadata, comments, files)
4. Map OKRs to PRs with intelligent AI-powered classification
5. Extract and organize PR comments
6. Classify PR comments using OpenAI into feedback categories
7. Aggregate PR statistics for each user into CSV files
8. Import PR statistics from CSV into SQLite database

## Features

- ✅ Automated task generation with incremental updates
- ✅ GitHub API integration with rate limiting and retry logic
- ✅ Batch processing for large datasets (10 PRs at a time)
- ✅ Progress tracking with status files
- ✅ Configurable base directory support
- ✅ Case-insensitive command-line arguments
- ✅ Intelligent PR-to-OKR mapping with AI (reads from SQLite database)
- ✅ PR comment extraction (authored/reviewed split)
- ✅ AI-powered comment classification (17 feedback categories)
- ✅ Cost tracking for OpenAI API usage
- ✅ Single batch mode for incremental processing
- ✅ PR stats aggregation and database import
- ✅ SQLite database integration for persistent storage

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
mkdir -p <base_dir>/{tasks,pr_data}
```

#### Configure `pipeline_config.json`
```json
{
  "base_dir": "/path/to/your/data",
  "pr_data_folder": "pr_data",
  "task_folder": "tasks",
  "pipeline": {
    "default_start_step": 1,
    "timeout_per_step_seconds": 1200,
    "continue_on_error": false
  }
}
```

#### Create `<base_dir>/settings.dev.json`
```json
{
  "org": "your-github-org",
  "integrations": {
    "github": {
      "pat": "ghp_your_token_here",
      "username": "your-github-username",
      "emuSuffix": "_GitHubOrg"
    }
  },
  "start_date": "2025-11-01",
  "openai_api_key": "sk-your-openai-key-here",
  "comment_classification_batch_size": 50,
  "comment_classification_single_batch_mode": false,
  "ai_reviewer_prefixes": ["github-actions", "svc-"]
}
```

#### Set up SQLite Database `<base_dir>/database.dev.db`
The database should contain:
- `users` table: User information (username, github_suffix, firstname, lastname)
- `goals` table: OKRs/goals (id, goal, start_date, end_date)
- `pr_stats` table: Aggregated PR statistics (auto-populated by pipeline)
- `pr_comment_details` table: Detailed comment classifications (future use)

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
| `--start-from N` | Start from step N (1-8) | `--start-from 2` |
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

4. **OKR Mapping** (`prOKRMapper.py`)
   - Maps OKRs (from SQLite database) to PRs using AI embeddings
   - Intelligent classification with fallback categories
   - Tracks OpenAI API costs
   - Creates `okrs_{username}.csv`

5. **Comment Generation** (`prCommentFileGenerator.py`)
   - Extracts PR comments for each user
   - Creates two files: authored PRs and reviewed PRs
   - Configurable username mapping

6. **Comment Classification** (`prCommentClassification.py`)
   - Classifies comments into 17 feedback categories
   - Uses OpenAI GPT-4o-mini for human comments
   - Skips AI for bot comments (no cost)
   - Batch processing with status tracking

7. **PR Stats Aggregation** (`prStatsAggregator.py`)
   - Aggregates PR statistics for each user
   - Combines authored and reviewed PR data with OKR mappings
   - Outputs CSV files to `pr_data/pr-stats/`
   - Creates status files for tracking

8. **Write Stats to DB** (`prStatsWriteToDB.py`)
   - Imports PR statistics from CSV files into SQLite database
   - Writes to `pr_stats` table
   - Deletes CSV files after successful import (configurable)
   - Tracks import progress

## Project Structure

```
falcon-python-backend/
├── common.py                      # Common utilities and config loading
├── githubCommonFunctions.py       # GitHub API interaction functions
├── prTaskGenerator.py             # Task generation script
├── prSearchTaskExecutor.py        # PR search and download script
├── prDownloadExecutor.py          # PR details download script
├── prOKRMapper.py                 # OKR-to-PR mapping script
├── prCommentFileGenerator.py      # Comment extraction script
├── prCommentClassification.py     # Comment classification script
├── prStatsAggregator.py           # PR stats aggregation script
├── prStatsWriteToDB.py            # Database import script
├── readUsers.py                   # Read users from SQLite database
├── readOKRs.py                    # Read OKRs from SQLite database
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
├── database.dev.db                # SQLite database
├── settings.dev.json              # Configuration (GitHub, OpenAI, dates)
├── tasks/                         # Task and status files
│   ├── pr_authored_user1.json
│   ├── pr_authored_user1_status.json
│   ├── pr_reviewer_user1.json
│   ├── pr_reviewer_user1_status.json
│   ├── pr_authored_user1_pr-aggregator_status.json
│   ├── pr_reviewer_user1_pr-aggregator_status.json
│   ├── user1_comments_classification_authored_status.json
│   └── user1_comments_classification_reviewed_status.json
└── pr_data/
    ├── search/                    # PR list CSV files
    │   └── pr_authored_user1_2025-11-01_2026-01-26.csv
    ├── comments/                  # Extracted comment files
    │   ├── user1_comments_on_authored_prs_2025-11-01_2026-01-26.csv
    │   └── user1_comments_on_reviewed_prs_2025-11-01_2026-01-26.csv
    ├── pr-stats/                  # Aggregated PR statistics (temporary CSV)
    │   └── pr_user1_2025-11-01_2026-01-26.csv
    └── {owner}/                   # Detailed PR data by repo
        └── {repo}/
            └── pr_{number}/
                ├── pr_{number}_meta.csv
                ├── pr_{number}_comments.csv
                ├── pr_{number}_files.csv
                └── okrs_user1.csv  # OKRs mapped to this PR
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
