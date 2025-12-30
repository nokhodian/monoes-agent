#!/usr/bin/env python3
"""
Generic action test script.
Runs any action for any platform and saves the results to a JSON file.
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import using internal names if running as script
try:
    from main import run_action
    from core.bot import get_bot_class
    from core.auth import AuthManager
    from core.runner import ActionRunner
    from src.database.database import DataBase
    from src.api.APIs import RestAPI
    from src.robot.flatlay import FlatLay
    from utils.logger import setup_enhanced_logging
except ImportError:
    # Fallback for different execution contexts
    from newAgent.main import run_action
    from newAgent.core.bot import get_bot_class
    from newAgent.core.auth import AuthManager
    from newAgent.core.runner import ActionRunner
    from newAgent.src.database.database import DataBase
    from newAgent.src.api.APIs import RestAPI
    from newAgent.src.robot.flatlay import FlatLay
    from newAgent.utils.logger import setup_enhanced_logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class MockAction:
    """Mock action object for testing."""
    def __init__(self, platform, action_type, **kwargs):
        self.source = platform.upper()
        self.type = action_type.upper()
        
        # Set all kwargs as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        # Specific mappings for known discrepancies/requirements
        if hasattr(self, 'keyword'):
            self.keywrd = self.keyword # Legacy support
            
        if hasattr(self, 'max_results'):
            self.maxResultsCount = int(self.max_results)
            
        if not hasattr(self, 'maxResultsCount'):
             self.maxResultsCount = 10 # Default

def run_test(platform, action_type, kwargs):
    print("=" * 60)
    print(f"TEST: {platform.upper()} {action_type.upper()}")
    print("=" * 60)
    print(f"Arguments: {kwargs}")
    print("=" * 60)
    
    # Initialize API and Database
    db = DataBase('MAC')
    api_token = db.fetch_setting("api_token", "")
    if api_token:
        print(f"  ✓ Loaded CRM API token from database")
        RestAPI.set_authorization(api_token)
        FlatLay.auth_with_bearer_token(api_token)
    else:
        print(f"  ⚠ No CRM API token found in database. Saving might fail.")

    # Initialize Bot
    print("\n[1/3] Initializing bot...")
    bot = None
    try:
        BotClass, login_url = get_bot_class(platform)
        bot = BotClass(login_url, 'MAC')
        bot._has_challenge = lambda: False
        bot.headless = kwargs.get('headless', False)
        
        auth = AuthManager(platform)
        auth.load_cookies(bot)
        
        print("  Initializing browser...")
        bot.web_driver(login_required=False)
        auth.check_and_save_login(bot)
        
    except Exception as e:
        print(f"✗ Failed to initialize bot: {e}")
        if bot:
            try: bot.quit()
            except: pass
        return None

    # Create action
    action = MockAction(platform, action_type, **kwargs)
    
    # Setup enhanced logging
    setup_enhanced_logging()
    
    # Execute
    print("\n[2/3] Executing action...")
    runner = ActionRunner(bot, action, api_client=RestAPI)
    result = runner.run()
    
    # Save results
    print("\n[3/3] Saving results...")
    
    # Ensure results directory exists
    results_dir = project_root / 'test_results'
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{platform}_{action_type}_{timestamp}.json"
    filepath = results_dir / filename
    
    # Sanitize result for JSON (some objects might not be serializable)
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(i) for i in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return str(obj)

    sanitized_result = sanitize(result)
    
    with open(filepath, 'w') as f:
        json.dump(sanitized_result, f, indent=4)
    
    print(f"✅ Results saved to: {filepath}")
    
    # Clean up
    if not kwargs.get('keep_open', False):
        try: bot.quit()
        except: pass
    else:
        print("\nBrowser remains open. Manual closure required.")
        
    return result

def main():
    parser = argparse.ArgumentParser(description='Generic Action Test Runner')
    parser.add_argument('platform', help='Platform name (instagram, linkedin, x, tiktok)')
    parser.add_argument('action_type', help='Action type (KEYWORD_SEARCH, etc.)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--keep-open', action='store_true', help='Keep browser open after test')
    parser.add_argument('args', nargs='*', help='Arguments in key=value format')

    args = parser.parse_args()
    
    kwargs = {
        'headless': args.headless,
        'keep_open': args.keep_open
    }
    
    for arg in args.args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Remove quotes
            if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                value = value[1:-1]
            # Convert to int if possible
            if value.isdigit():
                value = int(value)
            kwargs[key] = value

    run_test(args.platform, args.action_type, kwargs)

if __name__ == "__main__":
    main()
