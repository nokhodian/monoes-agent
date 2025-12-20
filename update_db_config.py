import sys
from pathlib import Path
import json

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from newAgent.src.services.config_manager import ConfigManager

def main():
    cm = ConfigManager(platform='MAC')
    
    # 1. Load and save the new config
    config_path = Path('newAgent/src/data/configs/LINKEDIN_SEARCH_PAGE.json')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        # Save as LINKEDIN_SEARCH_PAGE.json because active_configs points to this name
        cm._save_config_to_database('LINKEDIN_SEARCH_PAGE.json', config_data)
        print("Saved LINKEDIN_SEARCH_PAGE.json to DB")
    else:
        print(f"Config file not found: {config_path}")
        return

    # 2. Update active configs map
    active_configs_path = Path('newAgent/src/data/configs/active_configs.json')
    if active_configs_path.exists():
        with open(active_configs_path, 'r') as f:
            disk_active_configs = json.load(f)
        
        db_active_configs = cm.active_configs
        print(f"Current DB active configs: {db_active_configs}")
        
        # Update DB map with disk map
        db_active_configs.update(disk_active_configs)
        
        cm.active_configs = db_active_configs
        cm._save_active_configs()
        print(f"Updated active configs in DB: {cm.active_configs}")
    else:
        print(f"Active configs file not found: {active_configs_path}")

if __name__ == "__main__":
    main()
