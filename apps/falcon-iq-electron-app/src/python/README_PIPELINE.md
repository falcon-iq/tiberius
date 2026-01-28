# PR Data Pipeline Runner

A comprehensive orchestration tool for managing the PR data collection pipeline.

## Overview

The pipeline consists of seven sequential steps:

1. **Task Generation** (`prTaskGenerator.py`) - Creates PR tasks for each user based on configured date ranges
2. **PR Search** (`prSearchTaskExecutor.py`) - Downloads PR lists from GitHub using the search API
3. **PR Details Download** (`prDownloadExecutor.py`) - Downloads full PR details including metadata, comments, and files
4. **OKR Parsing** (`okrParser.py`) - Parses OKR files from okrs/input to okrs/parsed format
5. **OKR Mapping** (`prOKRMapper.py`) - Maps OKRs to PRs with intelligent classification and fallback
6. **Comment Generation** (`prCommentFileGenerator.py`) - Extracts and organizes PR comments (authored/reviewed)
7. **Comment Classification** (`prCommentClassification.py`) - Classifies PR comments using OpenAI into feedback categories

## Quick Start

### Run Full Pipeline
```bash
python runPipeline.py
```

### Use Custom Base Directory
```bash
# Override the base_dir from pipeline_config.json
# Supports multiple formats (case-insensitive, hyphen or underscore)
python runPipeline.py --base-dir /path/to/custom/data
python runPipeline.py --base_dir /path/to/custom/data
python runPipeline.py --BASE-DIR /path/to/custom/data
python runPipeline.py --Base_Dir /path/to/custom/data

# With specific steps
python runPipeline.py --base-dir /path/to/custom/data --steps 2,3
```

### Run from Specific Step
```bash
# Start from PR search (skip task generation)
python runPipeline.py --start-from 2

# Start from PR download (skip task generation and search)
python runPipeline.py --start-from 3
```

### Run Specific Steps Only
```bash
# Run only task generation
python runPipeline.py --steps 1

# Run only search and download
python runPipeline.py --steps 2,3

# Run task generation and download (skip search)
python runPipeline.py --steps 1,3
```

### List Available Steps
```bash
python runPipeline.py --list
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--base-dir PATH`<br>`--base_dir PATH` | Override base directory<br>(case-insensitive) | `--base-dir /custom/path`<br>`--BASE_DIR /custom/path` |
| `--start-from N` | Start from step N (1-7) | `--start-from 4` |
| `--steps X,Y,Z` | Run only specific steps | `--steps 1,3,5` |
| `--list` | List all available steps | `--list` |
| `-h, --help` | Show help message | `-h` |

### Base Directory Override

By default, the pipeline uses the `base_dir` specified in `pipeline_config.json`. You can override this for any run using the `--base-dir` option (accepts multiple formats - see examples below):

```bash
# Use a different data directory
python runPipeline.py --base-dir /path/to/different/data

# Useful for testing with separate data
python runPipeline.py --base-dir /tmp/test-data --steps 1

# Work with production data vs staging data
python runPipeline.py --base-dir /mnt/production-data
python runPipeline.py --base-dir /mnt/staging-data
```

**How it works:**
- The `--base-dir` option sets a global variable in `common.py`
- All scripts use this global override
- This affects all paths: `task_folder`, `pr_data_folder`, `settings_folder`, `okr_folder`, `comments_folder`, etc.
- The override only lasts for the current pipeline run

## Pipeline Steps Detail

### Step 1: Task Generation
- **Script**: `prTaskGenerator.py`
- **Purpose**: Generate PR tasks for users based on date ranges
- **Output**: Task files in `tasks/` folder with status tracking
- **Status**: Creates `pr_{type}_{username}.json` and `pr_{type}_{username}_status.json`

### Step 2: PR Search
- **Script**: `prSearchTaskExecutor.py`
- **Purpose**: Download PR lists from GitHub using search API
- **Input**: Task files from Step 1
- **Output**: CSV files with PR lists in `pr_data/search/`
- **Status**: Updates status to `pr-search-file-downloaded`

### Step 3: PR Details Download
- **Script**: `prDownloadExecutor.py`
- **Purpose**: Download full PR details (metadata, comments, files)
- **Input**: CSV files from Step 2
- **Output**: Detailed PR data in `pr_data/{owner}/{repo}/pr_{number}/`
- **Batch Processing**: Downloads 10 PRs at a time with progress tracking
- **Status**: Updates status to `pr-details-downloaded`

### Step 4: OKR Parsing
- **Script**: `okrParser.py`
- **Purpose**: Parse and structure OKR files for each user
- **Input**: Raw OKR files in `okrs/input/{username}_okrs.csv`
- **Output**: Parsed OKR files in `okrs/parsed/{username}_okrs_parsed.csv`
- **Features**: Extracts objective, key result, and metadata; handles multiple formats
- **Skip Logic**: Skips if parsed file already exists

### Step 5: OKR Mapping
- **Script**: `prOKRMapper.py`
- **Purpose**: Intelligently map OKRs to PRs with AI-powered classification
- **Input**: Parsed OKRs (Step 4) and PR data (Step 3)
- **Output**: `okrs_{username}.csv` with mapped PRs and classifications
- **Features**:
  - OpenAI embeddings for semantic matching
  - Hybrid scoring (embeddings + lexical + acronyms)
  - Fallback classification (cleanup, refactoring, dependency-updates)
  - Cost tracking and configurable thresholds
  - Force recalculation option via `user-settings.json`

### Step 6: Comment Generation
- **Script**: `prCommentFileGenerator.py`
- **Purpose**: Extract and organize PR comments for each user
- **Input**: PR data (Step 3) and task files
- **Output**: Two CSV files per user:
  - `{username}_comments_on_authored_prs_{date}.csv` - ALL comments on user's PRs
  - `{username}_comments_on_reviewed_prs_{date}.csv` - User's comments on others' PRs
- **Features**:
  - Configurable PR username mapping via `prUserName` in `users.json`
  - Includes comment metadata (type, author, PR details)
  - Skips if files already exist

### Step 7: Comment Classification
- **Script**: `prCommentClassification.py`
- **Purpose**: Classify PR comments using OpenAI into engineering feedback categories
- **Input**: Comment files from Step 6
- **Output**: Same CSV files with added classification columns
- **Categories**: 17 types (NITPICK_STYLE, BUG_CORRECTNESS, DESIGN_ARCHITECTURE, AI_GENERATED, etc.)
- **Features**:
  - Batch processing (configurable batch size, default 50)
  - Single batch mode for incremental processing
  - AI comment detection (skips OpenAI for bots - no cost)
  - Empty comment handling (classified as PRAISE_ACK)
  - Status tracking and automatic resume
  - Detailed cost tracking per batch and total
  - Caching to avoid duplicate classifications
- **Configuration**: Via `user-settings.json`:
  - `comment_classification_batch_size`: Comments per batch
  - `comment_classification_single_batch_mode`: Process one batch per run
  - `ai_reviewer_prefixes`: AI reviewer username prefixes

## Configuration

Pipeline configuration is stored in `pipeline_config.json`:

```json
{
  "base_dir": "/path/to/data",
  "task_folder": "tasks",
  "pr_data_folder": "pr_data",
  "pipeline": {
    "default_start_step": 1,
    "timeout_per_step_seconds": 600,
    "continue_on_error": false
  }
}
```

### Pipeline Settings

- `default_start_step`: Default step to start from (1-7)
- `timeout_per_step_seconds`: Maximum time allowed per step (default: 600s)
- `continue_on_error`: Whether to continue if a step fails (default: false)

## Error Handling

### Interactive Error Handling
When a step fails, the pipeline will:
1. Display the error message
2. Ask if you want to continue to the next step
3. Wait for user input (y/n)

### Non-Interactive Mode
To automatically stop on errors (recommended for automated runs), ensure `continue_on_error` is `false` in the config.

## Use Cases

### Initial Setup
Run all steps to set up the pipeline from scratch:
```bash
python runPipeline.py
```

### Working with Multiple Environments
Use different base directories for different environments:
```bash
# Production data
python runPipeline.py --base-dir /mnt/production/pr-data

# Staging/testing data
python runPipeline.py --base-dir /mnt/staging/pr-data

# Local development
python runPipeline.py --base-dir ~/local-test-data
```

### Daily Updates
If tasks are already generated, start from search:
```bash
python runPipeline.py --start-from 2
```

### Resume After Interruption
If search completed but download was interrupted:
```bash
python runPipeline.py --start-from 3
```

### Regenerate Tasks Only
If you need to regenerate tasks without running search/download:
```bash
python runPipeline.py --steps 1
```

### Testing with Custom Data
Test the pipeline with a separate data directory:
```bash
# Set up test environment
mkdir -p /tmp/test-pr-data/{tasks,pr_data,settings,user_data}
# ... copy necessary config files ...

# Run pipeline on test data
python runPipeline.py --base-dir /tmp/test-pr-data --steps 1,2
```

### Batch Processing
For large datasets, run Step 3 multiple times until complete:
```bash
# Downloads 10 PRs per run
python runPipeline.py --steps 3
python runPipeline.py --steps 3  # Repeat until all PRs are downloaded

# Or with custom base directory
python runPipeline.py --base-dir /custom/path --steps 3
```

## Output

### Pipeline Summary
After execution, you'll see a summary:
```
📊 PIPELINE SUMMARY
==================

   Step 1 (Task Generation): ✅ SUCCESS - 0.04s
   Step 2 (PR Search): ✅ SUCCESS - 12.35s
   Step 3 (PR Details Download): ✅ SUCCESS - 45.67s

   Total Steps Run: 3
   Successful: 3
   Failed: 0
   Total Duration: 58.06s

🎉 Pipeline completed successfully!
```

## Status Files

Each task has a status file that tracks progress:

```json
{
  "status": "pr-details-downloaded",
  "current_row": 32
}
```

**Status Values:**
- `not_started`: Task created but no work done
- `pr-search-file-downloaded`: PR list downloaded from GitHub
- `pr-details-downloaded`: All PR details downloaded
- `completed`: Task fully processed (used by task generator)

## Troubleshooting

### Pipeline Hangs
- Each step has a 10-minute timeout
- Check network connectivity for GitHub API calls
- Verify GitHub token is valid

### Step Fails
- Check the error message in the output
- Review individual script logs
- Verify configuration files are correct
- Ensure required folders exist

### Batch Download Not Progressing
- Step 3 downloads 10 PRs at a time
- Check `current_row` in status files to see progress
- Run multiple times until `status: "pr-details-downloaded"`

## Development

### Adding New Steps
To add a new pipeline step, edit `runPipeline.py`:

```python
STEPS = {
    1: {...},
    2: {...},
    3: {...},
    4: {  # New step
        "name": "Your Step Name",
        "script": "yourScript.py",
        "description": "What your step does"
    }
}
```

### Testing Individual Steps
Each script can be run independently:
```bash
python prTaskGenerator.py
python prSearchTaskExecutor.py
python prDownloadExecutor.py
```

## Best Practices

1. **Start Small**: Test with 1-2 users before scaling up
2. **Monitor Progress**: Check status files to track pipeline progress
3. **Incremental Runs**: Use batch processing for large datasets
4. **Error Recovery**: Use `--start-from` to resume after fixing issues
5. **Schedule Runs**: Use cron/scheduled tasks for automated updates

## Examples

### Complete Workflow for New User
```bash
# 1. Add user to user-settings.json
# 2. Run full pipeline
python runPipeline.py

# 3. If download interrupted, continue from Step 3
python runPipeline.py --start-from 3
```

### Daily Update Workflow
```bash
# Skip task generation if tasks exist
python runPipeline.py --start-from 2
```

### Troubleshooting Workflow
```bash
# Check what will run
python runPipeline.py --list

# Test individual step
python runPipeline.py --steps 2

# Run with fresh tasks
python runPipeline.py --steps 1,2,3
```
