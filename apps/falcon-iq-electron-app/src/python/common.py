"""
Common utilities for Falcon Python Backend

Provides functions to read configuration, users, and settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

# Global variable to override base_dir from config
# Check environment variable first, then default to None
_OVERRIDE_BASE_DIR: Optional[str] = os.environ.get('FALCON_BASE_DIR')
IS_DEV: bool = os.environ.get('FALCON_IS_DEV', '1') == '1'


def set_base_dir(base_dir: str):
    """
    Set the global base directory override.
    This will be used instead of the base_dir from pipeline_config.json.
    
    Args:
        base_dir: Path to the base directory
    """
    global _OVERRIDE_BASE_DIR
    _OVERRIDE_BASE_DIR = base_dir
    print(f"✅ Global base_dir set to: {base_dir}")

def set_env(is_dev: bool):
    """
    Set the global IS_DEV variable.
    
    Args:
        is_dev: Boolean indicating if in development mode
        """
    global IS_DEV
    IS_DEV = is_dev
    print(f"✅ Global IS_DEV set to: {IS_DEV}")


def get_base_dir() -> Optional[str]:
    """
    Get the current global base directory override.
    
    Returns:
        The override base_dir if set, None otherwise
    """
    return _OVERRIDE_BASE_DIR


def clear_base_dir():
    """Clear the global base directory override."""
    global _OVERRIDE_BASE_DIR
    _OVERRIDE_BASE_DIR = None


def load_pipeline_config(config_path: Optional[str] = None) -> Dict:
    """
    Load pipeline configuration.
    
    Args:
        config_path: Path to config file. If None, looks for pipeline_config.json in current dir
    
    Returns:
        Dictionary with configuration
    """
    if config_path is None:
        config_path = Path(__file__).parent / "pipeline_config.json"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)


def load_user_settings(base_dir: Path, settings_folder: str = "settings") -> Dict:
    """
    Load user settings from base directory.

    Args:
        base_dir: Base directory path
        settings_folder: Deprecated, kept for compatibility

    Returns:
        Dictionary with user settings
    """

    settings_file = "settings.dev.json" if IS_DEV else "settings.json"
    settings_path = base_dir / settings_file

    if not settings_path.exists():
        raise FileNotFoundError(f"User settings file not found: {settings_path}")

    with open(settings_path, 'r') as f:
        return json.load(f)


def get_github_token(settings: Dict) -> Optional[str]:
    """
    Get GitHub PAT from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        GitHub token or None if not found
    """
    try:
        return settings['integrations']['github']['pat']
    except (KeyError, TypeError):
        return None


def get_github_username(settings: Dict) -> Optional[str]:
    """
    Get GitHub username from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        GitHub username or None if not found
    """
    try:
        return settings['integrations']['github']['username']
    except (KeyError, TypeError):
        return None


def get_github_emu_suffix(settings: Dict) -> Optional[str]:
    """
    Get GitHub EMU suffix from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        GitHub EMU suffix or None if not found
    """
    try:
        return settings['integrations']['github']['emuSuffix']
    except (KeyError, TypeError):
        return None


def get_org(settings: Dict) -> Optional[str]:
    """
    Get organization from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        Organization name or None if not found
    """
    return settings.get('org')


def get_openai_api_key(settings: Dict) -> Optional[str]:
    """
    Get OpenAI API key from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        OpenAI API key or None if not found
    """
    return settings.get('openai_api_key')


def get_start_date(settings: Dict) -> Optional[str]:
    """
    Get start date from settings.
    
    Args:
        settings: Settings dictionary
    
    Returns:
        Start date or None if not found
    """
    return settings.get('start_date')


def get_ai_reviewer_prefixes(settings: Dict, default: Optional[List[str]] = None) -> List[str]:
    """
    Get AI reviewer prefixes from settings.
    
    Args:
        settings: Settings dictionary
        default: Default value if not found (defaults to ["github-actions", "svc-"])
    
    Returns:
        List of AI reviewer prefixes
    """
    if default is None:
        default = ["github-actions", "svc-"]
    return settings.get('ai_reviewer_prefixes', default)


def load_users(base_dir: Path, user_data_folder: str = "user_data") -> List[Dict]:
    """
    Load users from SQLite database.
    
    Args:
        base_dir: Base directory path
        user_data_folder: User data folder name (deprecated, kept for compatibility)
    
    Returns:
        List of user dictionaries with firstName, lastName, userName, prUserName
    """
    # Import here to avoid circular imports
    from readUsers import get_users_from_database
    
    # Database path: base_dir/database[.dev].db
    db_path = getDBPath(base_dir)
    
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")
    
    # Get users from database
    users = get_users_from_database(db_path, quiet=True)
    
    if not users:
        print(f"Warning: No users found in database: {db_path}")
        return []
    
    # Validate user schema
    required_fields = ['firstName', 'lastName', 'userName', 'prUserName']
    for i, user in enumerate(users):
        missing_fields = [field for field in required_fields if field not in user]
        if missing_fields:
            print(f"Warning: User {i} missing fields: {missing_fields}")
    
    return users


def get_user_by_username(users: List[Dict], username: str) -> Optional[Dict]:
    """
    Get a specific user by username.
    
    Args:
        users: List of user dictionaries
        username: Username to search for
    
    Returns:
        User dictionary or None if not found
    """
    for user in users:
        if user.get('userName') == username:
            return user
    return None


def get_base_dir() -> Path:
    """
    Get the base directory for Falcon IQ.
    Uses global base_dir override if set, otherwise uses config['base_dir'] from pipeline_config.json.
    
    Returns:
        Path to the base directory
    """
    # Use global override if set, otherwise use config
    if _OVERRIDE_BASE_DIR is not None:
        base_dir = Path(_OVERRIDE_BASE_DIR).expanduser()
    else:
        config = load_pipeline_config()
        base_dir = Path(config['base_dir']).expanduser()
    
    return base_dir


def getDBPath(base_dir: Path) -> Path:
    """
    Get the database file path based on the environment.
    
    Args:
        base_dir: Base directory path
    
    Returns:
        Path to the database file (database.dev.db in development, database.db in production)
    """
    database_file = "database.dev.db" if IS_DEV else "database.db"
    return base_dir / database_file


def initialize_paths(config: Dict) -> Dict[str, Path]:
    """
    Initialize all directory paths from config.
    Uses global base_dir override if set, otherwise uses config['base_dir'].
    
    Args:
        config: Configuration dictionary
    
    Returns:
        Dictionary mapping path names to Path objects
    """
    # Use global override if set, otherwise use config
    if _OVERRIDE_BASE_DIR is not None:
        base_dir = Path(_OVERRIDE_BASE_DIR).expanduser()
    else:
        base_dir = Path(config['base_dir']).expanduser()
    
    paths = {
        'base_dir': base_dir,
        'okr_folder': base_dir / config.get('okr_folder', 'okrs'),
        'pr_data_folder': base_dir / config.get('pr_data_folder', 'pr_data'),
        'task_folder': base_dir / config.get('task_folder', 'tasks'),
    }
    
    return paths


def load_all_config() -> Dict:
    """
    Load all configuration in one call.
    
    Returns:
        Dictionary with:
            - config: Pipeline configuration
            - settings: User settings
            - users: List of users
            - paths: Dictionary of Path objects
    """
    # Load pipeline config
    config = load_pipeline_config()
    
    # Initialize paths
    paths = initialize_paths(config)
    
    # Load user settings
    settings = load_user_settings(paths['base_dir'], config.get('settings_folder', 'settings'))
    
    # Load users
    users = load_users(paths['base_dir'], config.get('user_data_folder', 'user_data'))
    
    return {
        'config': config,
        'settings': settings,
        'users': users,
        'paths': paths
    }


# Example usage and testing
if __name__ == "__main__":
    print("=" * 80)
    print("📚 COMMON UTILITIES - TEST")
    print("=" * 80)
    
    try:
        # Test loading all config
        print("\n🔄 Loading all configuration...")
        all_config = load_all_config()
        
        print(f"\n✅ Configuration loaded successfully!")
        print(f"\n📋 Pipeline Config:")
        print(f"   Base dir: {all_config['paths']['base_dir']}")
        print(f"   Start date: {all_config['config'].get('start_date', 'N/A')}")
        
        print(f"\n⚙️  User Settings:")
        settings = all_config['settings']
        
        # Use helper functions to access nested values
        github_token = get_github_token(settings)
        github_username = get_github_username(settings)
        github_emu_suffix = get_github_emu_suffix(settings)
        org = get_org(settings)
        openai_key = get_openai_api_key(settings)
        start_date = get_start_date(settings)
        ai_prefixes = get_ai_reviewer_prefixes(settings)
        
        print(f"   version: {settings.get('version')}")
        print(f"   org: {org}")
        print(f"   start_date: {start_date}")
        print(f"   github_token: {github_token[:10] + '...' if github_token else 'NOT SET'}")
        print(f"   github_username: {github_username}")
        print(f"   github_emu_suffix: {github_emu_suffix}")
        print(f"   openai_api_key: {openai_key[:10] + '...' if openai_key else 'NOT SET'}")
        print(f"   ai_reviewer_prefixes: {ai_prefixes}")
        
        print(f"\n👥 Users ({len(all_config['users'])}):")
        for user in all_config['users']:
            print(f"   • {user['firstName']} {user['lastName']}")
            print(f"     userName: {user['userName']}")
            print(f"     prUserName: {user['prUserName']}")
        
        print(f"\n📁 Paths:")
        for name, path in all_config['paths'].items():
            exists = "✅" if path.exists() else "❌"
            print(f"   {name}: {path} {exists}")
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
