"""
Variable substitution system for action definitions.
Handles template variables like {{variable}} in action JSON files.
"""
import re
from typing import Dict, Any, Optional, List
from copy import deepcopy


class ActionVariableResolver:
    """Resolves template variables in action definitions."""
    
    # Pattern to match {{variable}} or {{variable.path}}
    VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        Initialize variable resolver with context.
        
        Args:
            context: Initial context dictionary for variable resolution
        """
        self.context = context or {}
    
    def set_context(self, context: Dict[str, Any]):
        """Update the resolution context."""
        self.context.update(context)
    
    def add_to_context(self, key: str, value: Any):
        """Add a single key-value pair to context."""
        self.context[key] = value
    
    def resolve(self, template: str) -> str:
        """
        Resolve all variables in a template string.
        
        Args:
            template: String containing variables like {{variable}} or {{item.url}}
            
        Returns:
            Resolved string with variables substituted
        """
        if not isinstance(template, str):
            return template
        
        def replace_var(match):
            var_path = match.group(1).strip()
            value = self._resolve_path(var_path)
            return str(value) if value is not None else ""
        
        return self.VARIABLE_PATTERN.sub(replace_var, template)
    
    def _resolve_path(self, path: str) -> Any:
        """
        Resolve a variable path (e.g., "item.url" or "messageText").
        
        Args:
            path: Dot-separated path to the value
            
        Returns:
            Resolved value or None if not found
        """
        # First, check if the full path exists as a key in variables (for keys like "extract_post_urls.data")
        if 'variables' in self.context:
            if path in self.context['variables']:
                return self.context['variables'][path]
        
        # Otherwise, try to navigate through the path
        parts = path.split('.')
        value = self.context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif isinstance(value, list):
                try:
                    index = int(part)
                    value = value[index] if 0 <= index < len(value) else None
                except ValueError:
                    value = None
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def get_variable(self, name: str) -> Any:
        """
        Get a variable value directly from context.
        
        Args:
            name: Variable name
            
        Returns:
            Variable value or None
        """
        return self.context.get(name)
    
    def resolve_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively resolve all variables in a dictionary.
        
        Args:
            data: Dictionary that may contain template variables
            
        Returns:
            Dictionary with all variables resolved
        """
        if not isinstance(data, dict):
            return data
        
        resolved = {}
        for key, value in data.items():
            resolved_key = self.resolve(key) if isinstance(key, str) else key
            
            if isinstance(value, str):
                # Check if the entire string is a single variable reference (e.g., "{{variable}}")
                # If so, preserve the original type instead of converting to string
                import re
                single_var_pattern = re.compile(r'^\{\{([^}]+)\}\}$')
                match = single_var_pattern.match(value)
                
                if match:
                    # It's a single variable reference - get the original value
                    var_path = match.group(1).strip()
                    resolved_value = self._resolve_path(var_path)
                    resolved[resolved_key] = resolved_value if resolved_value is not None else ""
                else:
                    # It's a template with text or multiple variables - resolve as string
                    resolved[resolved_key] = self.resolve(value)
            elif isinstance(value, dict):
                resolved[resolved_key] = self.resolve_dict(value)
            elif isinstance(value, list):
                resolved[resolved_key] = self.resolve_list(value)
            else:
                resolved[resolved_key] = value
        
        return resolved
    
    def resolve_list(self, data: List[Any]) -> List[Any]:
        """
        Recursively resolve all variables in a list.
        
        Args:
            data: List that may contain template variables
            
        Returns:
            List with all variables resolved
        """
        if not isinstance(data, list):
            return data
        
        resolved = []
        for item in data:
            if isinstance(item, str):
                resolved.append(self.resolve(item))
            elif isinstance(item, dict):
                resolved.append(self.resolve_dict(item))
            elif isinstance(item, list):
                resolved.append(self.resolve_list(item))
            else:
                resolved.append(item)
        
        return resolved
    
    def extract_variables(self, template: str) -> List[str]:
        """
        Extract all variable names from a template string.
        
        Args:
            template: String containing variables
            
        Returns:
            List of variable paths found in template
        """
        if not isinstance(template, str):
            return []
        
        matches = self.VARIABLE_PATTERN.findall(template)
        return [match.strip() for match in matches]


def create_resolver(action: Any, saved_item: Optional[Any] = None, 
                   campaign: Optional[Any] = None) -> ActionVariableResolver:
    """
    Create a variable resolver with common context variables.
    
    Args:
        action: Action object with properties
        saved_item: SavedItem object (for loops)
        campaign: Campaign object
        
    Returns:
        Configured ActionVariableResolver
    """
    context = {}
    
    # Add action properties
    if action:
        if hasattr(action, 'messageText'):
            context['messageText'] = action.messageText
        if hasattr(action, 'messageSubject'):
            context['messageSubject'] = action.messageSubject
        if hasattr(action, 'keywrd'):
            context['keyword'] = action.keywrd
        if hasattr(action, 'text'):
            context['text'] = action.text
        if hasattr(action, 'commentText'):
            context['commentText'] = action.commentText
        if hasattr(action, 'maxResultsCount'):
            context['maxResultsCount'] = action.maxResultsCount
        if hasattr(action, 'selectedListItems'):
            context['selectedListItems'] = action.selectedListItems
    
    # Add saved item properties (for iteration)
    if saved_item:
        context['item'] = {
            'url': getattr(saved_item, 'url', ''),
            'id': getattr(saved_item, 'id', ''),
            'platform_username': getattr(saved_item, 'platform_username', ''),
            'full_name': getattr(saved_item, 'full_name', ''),
            'first_name': getattr(saved_item, 'first_name', ''),
            'last_name': getattr(saved_item, 'last_name', ''),
        }
        # Add variables from saved_item
        if hasattr(saved_item, 'variables'):
            context['item'].update(saved_item.variables)
    
    # Add current_url as a special variable (will be resolved dynamically)
    context['current_url'] = None  # Will be resolved by executor
    
    # Add campaign properties
    if campaign:
        context['campaign'] = {
            'title': getattr(campaign, 'title', ''),
            'campaignID': getattr(campaign, 'campaignID', ''),
            'brief_description': getattr(campaign, 'brief_description', '')
        }
    
    return ActionVariableResolver(context)

