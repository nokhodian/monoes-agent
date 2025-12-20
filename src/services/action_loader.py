"""
Action definition loader.
Loads and caches action definitions from JSON files.
"""
import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from newAgent.src.services.action_schema import validate_action_file

logger = logging.getLogger(__name__)


class ActionLoader:
    """Loads and caches action definitions from JSON files."""
    
    def __init__(self, actions_dir: Optional[str] = None):
        """
        Initialize action loader.
        
        Args:
            actions_dir: Base directory for action JSON files.
                        Defaults to src/data/actions/
        """
        if actions_dir is None:
            # Default to src/data/actions/ relative to this file
            base_dir = Path(__file__).parent.parent
            actions_dir = str(base_dir / "data" / "actions")
        
        self.actions_dir = Path(actions_dir)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ensure_actions_dir()
    
    def _ensure_actions_dir(self):
        """Create actions directory if it doesn't exist."""
        if not self.actions_dir.exists():
            self.actions_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created actions directory: {self.actions_dir}")
    
    def load_action(self, platform: str, action_type: str, 
                   use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load an action definition from JSON file.
        
        Args:
            platform: Platform name (e.g., "LINKEDIN", "INSTAGRAM")
            action_type: Action type (e.g., "BULK_MESSAGING", "KEYWORD_SEARCH")
            use_cache: Whether to use cached version if available
            
        Returns:
            Action definition dictionary or None if not found/invalid
        """
        cache_key = f"{platform.upper()}_{action_type.upper()}"
        
        # Check cache first
        if use_cache and cache_key in self._cache:
            logger.debug(f"Loading {cache_key} from cache")
            return self._cache[cache_key]
        
        # Construct file path
        platform_dir = self.actions_dir / platform.lower()
        file_path = platform_dir / f"{action_type.upper()}.json"
        
        if not file_path.exists():
            logger.warning(f"Action file not found: {file_path}")
            return None
        
        # Validate and load
        is_valid, error = validate_action_file(str(file_path))
        if not is_valid:
            logger.error(f"Invalid action definition in {file_path}: {error}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                action_data = json.load(f)
            
            # Verify platform and actionType match
            if action_data.get('platform', '').upper() != platform.upper():
                logger.warning(f"Platform mismatch in {file_path}: expected {platform}, got {action_data.get('platform')}")
            
            if action_data.get('actionType', '').upper() != action_type.upper():
                logger.warning(f"ActionType mismatch in {file_path}: expected {action_type}, got {action_data.get('actionType')}")
            
            # Cache the loaded action
            if use_cache:
                self._cache[cache_key] = action_data
            
            logger.info(f"Loaded action definition: {cache_key}")
            return action_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading action from {file_path}: {e}")
            return None
    
    def list_actions(self, platform: Optional[str] = None) -> Dict[str, list]:
        """
        List all available action definitions.
        
        Args:
            platform: Optional platform filter. If None, lists all platforms.
            
        Returns:
            Dictionary mapping platform names to lists of action types
        """
        actions = {}
        
        if platform:
            platforms = [platform.lower()]
        else:
            platforms = [d.name for d in self.actions_dir.iterdir() if d.is_dir()]
        
        for platform_name in platforms:
            platform_dir = self.actions_dir / platform_name
            if not platform_dir.exists():
                continue
            
            action_types = []
            for file_path in platform_dir.glob("*.json"):
                action_type = file_path.stem.upper()
                action_types.append(action_type)
            
            if action_types:
                actions[platform_name.upper()] = sorted(action_types)
        
        return actions
    
    def clear_cache(self, platform: Optional[str] = None, 
                   action_type: Optional[str] = None):
        """
        Clear action definition cache.
        
        Args:
            platform: Optional platform filter
            action_type: Optional action type filter
        """
        if platform and action_type:
            cache_key = f"{platform.upper()}_{action_type.upper()}"
            self._cache.pop(cache_key, None)
        elif platform:
            # Clear all actions for platform
            keys_to_remove = [k for k in self._cache.keys() 
                            if k.startswith(f"{platform.upper()}_")]
            for key in keys_to_remove:
                self._cache.pop(key, None)
        else:
            # Clear all cache
            self._cache.clear()
        
        logger.debug(f"Cache cleared for platform={platform}, action_type={action_type}")
    
    def reload_action(self, platform: str, action_type: str) -> Optional[Dict[str, Any]]:
        """
        Force reload an action definition (bypasses cache).
        
        Args:
            platform: Platform name
            action_type: Action type
            
        Returns:
            Action definition dictionary or None
        """
        self.clear_cache(platform, action_type)
        return self.load_action(platform, action_type, use_cache=True)


# Global instance
_action_loader: Optional[ActionLoader] = None


def get_action_loader() -> ActionLoader:
    """Get or create global action loader instance."""
    global _action_loader
    if _action_loader is None:
        _action_loader = ActionLoader()
    return _action_loader




