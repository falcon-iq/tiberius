# PR Analytics Agent - Integration with Existing Infrastructure

This document explains how the PR Analytics Agent integrates with the existing Falcon IQ infrastructure.

## Configuration Integration

### Settings File

The agent **reuses the existing settings infrastructure** from `common.py`:

```python
# In app/config.py
from common import (
    get_base_dir,
    getDBPath,
    load_user_settings,
    get_openai_api_key,
    get_github_username,
    IS_DEV
)
```

### How It Works

1. **Base Directory**: Uses `get_base_dir()` from `common.py`
   - Respects `FALCON_BASE_DIR` environment variable
   - Falls back to `pipeline_config.json` base_dir
   - Default: `~/Library/Application Support/Falcon IQ`

2. **Database Path**: Uses `getDBPath()` from `common.py`
   - Development: `database.dev.db`
   - Production: `database.db`

3. **Settings File**: Uses `load_user_settings()` from `common.py`
   - Development: `settings.dev.json`
   - Production: `settings.json`

4. **OpenAI API Key**: Uses `get_openai_api_key()` from `common.py`
   - Reads `openai_api_key` from settings file
   - Falls back to `OPENAI_API_KEY` environment variable

5. **Default Username**: Uses `get_github_username()` from `common.py`
   - Reads from `settings.integrations.github.username`
   - Falls back to `FALCON_USERNAME` environment variable

## No Duplicate Configuration

The agent **does NOT duplicate** any configuration logic:
- ✅ Uses existing base directory resolution
- ✅ Uses existing settings file structure
- ✅ Uses existing database path logic
- ✅ Uses existing API key retrieval

## Example Settings File

The agent works with your existing `settings.dev.json`:

```json
{
  "openai_api_key": "sk-your-key-here",
  "integrations": {
    "github": {
      "username": "npurwar",
      "pat": "ghp_your-github-token",
      "emuSuffix": "_corp"
    }
  }
}
```

## Environment Variables (Optional Overrides)

You can override settings via environment variables:

```bash
# Override OpenAI API key
export OPENAI_API_KEY="sk-override-key"

# Override username  
export FALCON_USERNAME="other-user"

# Override base directory
export FALCON_BASE_DIR="/custom/path"

# Override dev mode
export FALCON_IS_DEV="0"  # Use production database
```

## Usage

### With Existing Settings (Recommended)
```bash
# Just run the agent - it reads your existing settings
cd apps/falcon-iq-electron-app/src/python
python -m app.main "What are my top PRs?"
```

### Verify Configuration
```bash
# Check that settings are loaded correctly
python -m app.verify_setup
```

### Check What Settings Are Used
```bash
python -c "
from app.config import BASE_DIR, SQLITE_PATH, DEFAULT_USERNAME, get_api_key
print(f'Base Dir: {BASE_DIR}')
print(f'Database: {SQLITE_PATH}')
print(f'Username: {DEFAULT_USERNAME}')
print(f'API Key: {\"Found\" if get_api_key() else \"Not Found\"}')
"
```

## Benefits of Integration

1. **Single Source of Truth**: All Falcon IQ components use the same settings
2. **No Duplication**: No need to maintain separate configuration
3. **Consistent Behavior**: Agent behaves like other Falcon IQ scripts
4. **Easy Onboarding**: If settings are already configured, agent works immediately
5. **Flexible Overrides**: Environment variables work for testing/CI

## Implementation Details

### Path Resolution

The agent imports from parent directory to access `common.py`:

```python
# In app/config.py
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))

from common import get_base_dir, load_user_settings, ...
```

### Lazy Loading

Settings are loaded lazily and cached:

```python
_settings: Optional[Dict] = None

def get_settings() -> Dict:
    """Load settings from settings file (cached)."""
    global _settings
    if _settings is None:
        _settings = load_user_settings(BASE_DIR)
    return _settings
```

### API Key Retrieval

```python
def get_api_key() -> Optional[str]:
    """Get OpenAI API key from settings file."""
    settings = get_settings()
    api_key = get_openai_api_key(settings)
    if not api_key:
        # Fallback to environment variable
        api_key = os.environ.get('OPENAI_API_KEY')
    return api_key
```

## Testing

The agent's test suite includes tests for:
- SQL validation (independent of settings)
- Database tools (uses temporary test database)
- Configuration loading (mocked in tests)

Run tests:
```bash
pytest tests/ -v
```

## Migration Notes

If you previously set `OPENAI_API_KEY` as an environment variable:
- ✅ Still works (fallback behavior)
- ✅ But better to add to settings file (consistent with other tools)
- ✅ Settings file takes precedence over environment variable

## Summary

The PR Analytics Agent is a **native Falcon IQ component** that:
- Reads the same settings file as other scripts
- Uses the same database as the pipeline
- Follows the same configuration patterns
- Requires no additional setup if Falcon IQ is already configured

---

**No changes needed to existing configuration!** If your Falcon IQ setup works, the agent works too.
