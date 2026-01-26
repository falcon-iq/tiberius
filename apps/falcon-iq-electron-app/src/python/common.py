"""
Common utilities for Falcon Python Backend

Provides functions to read configuration, users, and settings.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


# Global variable to override base_dir from config
_OVERRIDE_BASE_DIR: Optional[str] = None


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
    Load user settings from settings folder.
    
    Args:
        base_dir: Base directory path
        settings_folder: Settings folder name (default: "settings")
    
    Returns:
        Dictionary with user settings
    """
    settings_path = base_dir / settings_folder / "user-settings.json"
    
    if not settings_path.exists():
        raise FileNotFoundError(f"User settings file not found: {settings_path}")
    
    with open(settings_path, 'r') as f:
        return json.load(f)


def load_users(base_dir: Path, user_data_folder: str = "user_data") -> List[Dict]:
    """
    Load users from user_data folder.
    
    Args:
        base_dir: Base directory path
        user_data_folder: User data folder name (default: "user_data")
    
    Returns:
        List of user dictionaries with firstName, lastName, userName, prUserName
    """
    users_path = base_dir / user_data_folder / "users.json"
    
    if not users_path.exists():
        raise FileNotFoundError(f"Users file not found: {users_path}")
    
    with open(users_path, 'r') as f:
        users = json.load(f)
    
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
        'output_folder': base_dir / config.get('output_folder', 'output'),
        'pr_data_folder': base_dir / config.get('pr_data_folder', 'pr_data'),
        'user_data_folder': base_dir / config.get('user_data_folder', 'user_data'),
        'settings_folder': base_dir / config.get('settings_folder', 'settings'),
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
        for key, value in all_config['settings'].items():
            # Mask sensitive data
            if 'token' in key.lower() or 'key' in key.lower():
                value = value[:10] + "..." if isinstance(value, str) and len(value) > 10 else "***"
            print(f"   {key}: {value}")
        
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
