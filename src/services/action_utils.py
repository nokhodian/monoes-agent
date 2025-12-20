"""
Utility functions for working with JSON action definitions.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from newAgent.src.services.action_loader import get_action_loader
from newAgent.src.services.action_schema import validate_action_file


def list_all_actions(platform: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List all available action definitions.
    
    Args:
        platform: Optional platform filter
        
    Returns:
        Dictionary mapping platforms to lists of action types
    """
    loader = get_action_loader()
    return loader.list_actions(platform)


def get_action_info(platform: str, action_type: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific action definition.
    
    Args:
        platform: Platform name
        action_type: Action type
        
    Returns:
        Action definition dictionary or None
    """
    loader = get_action_loader()
    return loader.load_action(platform, action_type)


def validate_all_actions() -> Dict[str, Any]:
    """
    Validate all action definitions and return results.
    
    Returns:
        Dictionary with validation results
    """
    from newAgent.src.services.validate_actions import validate_all_actions as validate
    
    results = {
        'valid': [],
        'invalid': [],
        'total': 0
    }
    
    loader = get_action_loader()
    all_actions = loader.list_actions()
    
    for platform, action_types in all_actions.items():
        for action_type in action_types:
            results['total'] += 1
            action_def = loader.load_action(platform, action_type, use_cache=False)
            
            if action_def:
                # Validate structure
                from newAgent.src.services.action_schema import validate_action
                is_valid, error = validate_action(action_def)
                
                if is_valid:
                    results['valid'].append(f"{platform}/{action_type}")
                else:
                    results['invalid'].append({
                        'action': f"{platform}/{action_type}",
                        'error': error
                    })
            else:
                results['invalid'].append({
                    'action': f"{platform}/{action_type}",
                    'error': 'Could not load action definition'
                })
    
    return results


def get_action_steps(platform: str, action_type: str) -> List[Dict[str, Any]]:
    """
    Get list of steps for an action.
    
    Args:
        platform: Platform name
        action_type: Action type
        
    Returns:
        List of step definitions
    """
    action_def = get_action_info(platform, action_type)
    if action_def:
        return action_def.get('steps', [])
    return []


def find_step_by_id(platform: str, action_type: str, step_id: str) -> Optional[Dict[str, Any]]:
    """
    Find a specific step by ID in an action definition.
    
    Args:
        platform: Platform name
        action_type: Action type
        step_id: Step ID to find
        
    Returns:
        Step definition or None
    """
    steps = get_action_steps(platform, action_type)
    for step in steps:
        if step.get('id') == step_id:
            return step
    return None




