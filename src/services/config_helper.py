from typing import Dict, Optional

class ConfigHelper:
    @staticmethod
    def get_xpath(config: Dict, field_name: str) -> Optional[str]:
        """
        Search for a field by name in the config and return its xpath.
        Performs a recursive search.
        """
        if not config:
            print(f"DEBUG ConfigHelper: No config structure found")
            return None

        # Try 'config' key, 'fields' key, or use the whole object
        if 'config' in config:
            root = config['config'].get('fields', config['config'])
        elif 'fields' in config:
            root = config['fields']
        else:
            root = config

        print(f"DEBUG ConfigHelper: Searching for '{field_name}' in config root: {root.get('name', 'unnamed')}")
        result = ConfigHelper._find_xpath_recursive(root, field_name)
        print(f"DEBUG ConfigHelper: Found XPath for '{field_name}': {result}")
        return result

    @staticmethod
    def _find_xpath_recursive(node: Dict, target_name: str) -> Optional[str]:
        # Check if current node is the target
        if node.get('name') == target_name:
            return node.get('xpath')
        
        # Check children
        if 'data' in node and isinstance(node['data'], list):
            for child in node['data']:
                result = ConfigHelper._find_xpath_recursive(child, target_name)
                if result:
                    return result
        
        return None
