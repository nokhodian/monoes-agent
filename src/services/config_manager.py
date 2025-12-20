import os
import json
import logging
import time
from typing import Dict, Any, Optional
from newAgent.src.services.api_client import APIClient

logger = logging.getLogger(__name__)

class ConfigManager:
    ACTIVE_CONFIGS_KEY = "active_configs_map"

    def __init__(self, platform: str = None, database=None):
        """
        Initialize ConfigManager with database storage.
        
        Args:
            platform: Platform string ('MAC', 'WINDOWS', etc.) - required if database not provided
            database: Optional DataBase instance - if not provided, will create one using platform
        """
        self.api = APIClient()
        
        # Initialize database connection
        if database is not None:
            self.db = database
        elif platform is not None:
            from newAgent.src.database.database import DataBase
            self.db = DataBase(platform)
        else:
            # Default to MAC if nothing provided (for backward compatibility)
            # But this should ideally be avoided - platform should be provided
            logger.warning("ConfigManager initialized without platform or database. Defaulting to MAC.")
            from newAgent.src.database.database import DataBase
            self.db = DataBase('MAC')
        
        self.active_configs = self._load_active_configs()

    def _load_active_configs(self) -> Dict[str, str]:
        """Load active configs mapping from database"""
        try:
            active_configs_json = self.db.fetch_setting(self.ACTIVE_CONFIGS_KEY)
            if active_configs_json:
                return json.loads(active_configs_json)
        except Exception as e:
            logger.error(f"Failed to load active configs from database: {e}")
        return {}

    def _save_active_configs(self):
        """Save active configs mapping to database"""
        try:
            active_configs_json = json.dumps(self.active_configs)
            self.db.save_setting(self.ACTIVE_CONFIGS_KEY, active_configs_json)
        except Exception as e:
            logger.error(f"Failed to save active configs to database: {e}")

    def _save_config_to_database(self, config_name: str, config_data: Dict):
        """Save config to database instead of disk"""
        try:
            self.db.save_config(config_name, config_data)
            logger.debug(f"Saved config {config_name} to database")
        except Exception as e:
            logger.error(f"Failed to save config {config_name} to database: {e}")

    def _load_config_from_database(self, config_name: str) -> Optional[Dict]:
        """Load a configuration from the database."""
        try:
            print(f"📡 DB Lookup: config_name={config_name}")
            config_data = self.db.fetch_config(config_name)
            if config_data:
                print(f"✅ DB Match: Found config {config_name}")
                return config_data
            print(f"❌ DB Miss: Config {config_name} not found")
        except Exception as e:
            logger.error(f"Failed to load config {config_name} from database: {e}")
        return None

    def _load_config_from_local_file(self, config_name: str) -> Optional[Dict]:
        """Load a configuration from a local file."""
        import os
        import json
        try:
            config_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'configs'))
            config_path = os.path.join(config_dir, config_name)
            if os.path.exists(config_path):
                print(f"📂 Local File Lookup: path={config_path}")
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                    print(f"✅ Local File Match: Found config {config_name}")
                    return config_data
        except Exception as e:
            logger.error(f"Failed to load local config {config_name}: {e}")
        return None


    def get_config(self, social: str, action: str, config_context: Optional[str] = None,
                   html_content: str = "", purpose: str = "", schema: Optional[Dict] = None,
                   force_refresh: bool = False) -> Optional[Dict]:
        """
        Get or generate config for extracting data from HTML.
        Standardizes platform name to uppercase.
        """
        social = social.upper()
        # Build context-aware config name
        if config_context:
            # Use context-specific naming for multi-page actions
            base_name = f"{social}_{config_context.upper()}"
        else:
            # Use action-based naming for single-page actions
            base_name = f"{social}_{action.upper()}"

        print(f"DEBUG ConfigManager: social={social}, action={action}, base_name={base_name}, context={config_context}")
        logger.info(f"Getting config for: {base_name} (context: {config_context or 'none'})")
        
        # 1. Try to get existing active config
        if not force_refresh and base_name in self.active_configs:
            full_config_name = self.active_configs[base_name]
            print(f"DEBUG ConfigManager: Attempting to load active config '{full_config_name}' for base_name '{base_name}'")
            # Try local file first during development
            config = self._load_config_from_local_file(full_config_name)
            if not config:
                config = self._load_config_from_database(full_config_name)
            
            if config:
                print(f"✅ ConfigManager: Found active config {full_config_name} for {base_name}")
                return config
            else:
                print(f"⚠️ ConfigManager: Active config {full_config_name} not found in DB. Refreshing.")
                logger.warning(f"Active config {full_config_name} not found in database. Refreshing.")
        else:
            print(f"DEBUG ConfigManager: No active config found for '{base_name}' or force_refresh is true. Proceeding to test/generate.")

        
        # 2. Use extracttest to find best existing config (only if HTML provided)
        if not html_content:
            logger.warning(f"No HTML content provided for config {base_name}, cannot test or generate")
            print(f"❌ No HTML content provided for {base_name}")
            return None

        logger.info(f"Running extracttest for {base_name}")
        print(f"🔍 Testing existing configs for {base_name}...")
        test_results = self.api.extract_test(base_name, html_content)

        best_config_name = None
        max_score = 0

        if test_results:
            print(f"✅ Found {len(test_results)} existing configs to test")
            # Sort by fieldsWithValue descending
            test_results.sort(key=lambda x: x.get('fieldsWithValue', 0), reverse=True)
            best_result = test_results[0]
            if best_result.get('fieldsWithValue', 0) > 0:
                best_config_name = best_result.get('configName')
                max_score = best_result.get('fieldsWithValue')

        # 3. If good config found, fetch and use it
        if best_config_name:
            logger.info(f"Found existing config {best_config_name} with score {max_score}")
            print(f"✅ Using existing config: {best_config_name} (score: {max_score})")
            config_data = self.api.get_config(best_config_name)
            if config_data:
                self._save_config_to_database(best_config_name, config_data)
                self.active_configs[base_name] = best_config_name
                self._save_active_configs()
                return config_data
            else:
                print(f"❌ Failed to fetch config {best_config_name}")
        else:
            print(f"⚠️  No existing configs found with good scores")

        # 4. If no good config, generate new one
        logger.info(f"No valid config found. Generating new config for {base_name}")
        print(f"🔨 Generating new config for {base_name}...")

        # Use provided schema or empty dict as fallback
        extraction_schema = schema if schema else {}

        new_config = self.api.generate_config(base_name, html_content, purpose, extraction_schema)

        if new_config and 'configName' in new_config:
            print(f"✅ Successfully generated new config")
            new_config_name = new_config['configName']
            # The API might return the wrapper or the config inside. 
            # Based on docs, generate-config response is the config structure with configName inside? 
            # Or does it return the JSON with 'configName' and 'config'?
            # Let's assume the response IS the config object or contains it.
            # Adjusting based on reading: "generate-config response" showed:
            # { "configName": "...", "config": { ... } }
            
            self._save_config_to_database(new_config_name, new_config)
            self.active_configs[base_name] = new_config_name
            self._save_active_configs()
            return new_config
        
        logger.error("Failed to obtain a configuration from API.")
        print(f"⚠️  API config methods failed for {base_name}")
        print(f"   - API test results: {test_results is not None and len(test_results) > 0 if test_results else False}")
        print(f"   - Config generation: {new_config is not None}")

        # FALLBACK: Try to load from local config files
        print(f"🔍 Trying to load config from local files...")
        import os
        import json
        import glob

        config_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'configs')
        pattern = os.path.join(config_dir, f"{base_name}*.json*")
        matching_files = glob.glob(pattern)

        if matching_files:
            # Use the most recent file
            matching_files.sort(key=os.path.getmtime, reverse=True)
            config_file = matching_files[0]
            print(f"✅ Found local config file: {os.path.basename(config_file)}")
            try:
                with open(config_file, 'r') as f:
                    local_config = json.load(f)
                    print(f"✅ Successfully loaded config from local file")
                    return local_config
            except Exception as e:
                print(f"❌ Failed to load local config: {e}")

        print(f"❌ No local config files found matching {base_name}")
        return None

    def invalidate_config(self, social: str, action: str):
        base_name = f"{social.upper()}_{action.upper()}"
        if base_name in self.active_configs:
            logger.info(f"Invalidating config for {base_name}")
            del self.active_configs[base_name]
            self._save_active_configs()

    def invalidate_config_by_base_name(self, base_name: str):
        """Invalidate config by base name directly (for API use)"""
        base_name = base_name.upper()
        if base_name in self.active_configs:
            logger.info(f"Invalidating config for {base_name}")
            del self.active_configs[base_name]
            self._save_active_configs()
        else:
            logger.warning(f"Config {base_name} not found in active configs")

