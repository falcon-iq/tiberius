"""Configuration for PR Analytics Agent."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path to import common.py
_PARENT_DIR = Path(__file__).parent.parent
if str(_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(_PARENT_DIR))

# Import from existing common.py
from common import (
    get_base_dir as _get_base_dir,
    getDBPath,
    load_user_settings,
    get_openai_api_key,
    get_github_username,
    IS_DEV
)

# Get base directory using existing logic
BASE_DIR = _get_base_dir()

# SQLite database path using existing logic
SQLITE_PATH = getDBPath(BASE_DIR)

# Load settings and get configuration
_settings: Optional[Dict] = None

def get_settings() -> Dict:
    """Load settings from settings file (cached)."""
    global _settings
    if _settings is None:
        try:
            _settings = load_user_settings(BASE_DIR)
        except FileNotFoundError as e:
            print(f"⚠️  Warning: {e}")
            print(f"   Please create a settings file at {BASE_DIR}/settings{'dev' if IS_DEV else ''}.json")
            _settings = {}
    return _settings

# Get OpenAI API key from settings
def get_api_key() -> Optional[str]:
    """Get OpenAI API key from settings file."""
    settings = get_settings()
    api_key = get_openai_api_key(settings)
    if not api_key:
        # Fallback to environment variable
        api_key = os.environ.get('OPENAI_API_KEY')
    return api_key

# Default username from settings or environment
def get_default_username() -> str:
    """Get default username from settings or environment."""
    settings = get_settings()
    username = get_github_username(settings)
    if not username:
        username = os.environ.get('FALCON_USERNAME', 'npurwar')
    return username

DEFAULT_USERNAME = get_default_username()

# Query limits
MAX_QUERY_LIMIT = 200
DEFAULT_QUERY_LIMIT = 20

# OpenAI settings
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.0

# Validation settings
ALLOWED_KEYWORDS = {'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 
                    'OUTER', 'ON', 'AS', 'AND', 'OR', 'NOT', 'IN', 'LIKE', 
                    'BETWEEN', 'IS', 'NULL', 'ORDER', 'BY', 'GROUP', 'HAVING',
                    'LIMIT', 'OFFSET', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 
                    'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
                    'CAST', 'COALESCE', 'IFNULL', 'SUBSTR', 'LENGTH', 'LOWER',
                    'UPPER', 'TRIM', 'REPLACE', 'ROUND', 'ABS', 'DATETIME',
                    'DATE', 'STRFTIME', 'JULIANDAY'}

DANGEROUS_KEYWORDS = {'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
                      'TRUNCATE', 'PRAGMA', 'ATTACH', 'DETACH', 'VACUUM',
                      'REINDEX', 'EXEC', 'EXECUTE', 'CALL', 'IMPORT', 'LOAD'}
