#!/usr/bin/env python3
"""
NewAgent CLI Tool
Unified interface for running actions, managing sessions, and testing bots.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from newAgent.core.bot import get_bot_class
from newAgent.core.auth import AuthManager
from newAgent.core.runner import ActionRunner
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
             
        # For LinkedIn keyword search specifically
        if self.source == 'LINKEDIN' and self.type == 'KEYWORD_SEARCH':
            if not hasattr(self, 'keyword'):
                 print("Warning: LinkedIn KEYWORD_SEARCH requires 'keyword' argument")

def main():
    # Pre-process args to handle implicit 'run' command
    if len(sys.argv) > 1 and sys.argv[1] not in ['run', 'list', '-h', '--help']:
        # If the first arg is not a command, assume it's 'run' and insert it
        sys.argv.insert(1, 'run')

    parser = argparse.ArgumentParser(description='NewAgent CLI: Run actions and manage bots.')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run an action')
    run_parser.add_argument('platform', help='Platform name (instagram, linkedin, x, tiktok)')
    run_parser.add_argument('action_type', help='Action type (KEYWORD_SEARCH, BULK_MESSAGING, etc.)')
    run_parser.add_argument('args', nargs='*', help='Arguments in key=value format (e.g. keyword="python")')
    
    # List command (placeholder for future feature)
    list_parser = subparsers.add_parser('list', help='List available actions')
    list_parser.add_argument('platform', help='Platform name')

    args = parser.parse_args()
    
    if args.command == 'list':
        # TODO: Implement listing logic reading from src/data/actions
        print(f"Listing actions for {args.platform} (Not implemented yet)")
        sys.exit(0)
        
    if args.command == 'run':
        # Parse generic args
        kwargs = {}
        for arg in args.args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                # Remove quotes if present
                if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                
                # Try to convert to int if possible
                try:
                    if value.isdigit():
                        value = int(value)
                except ValueError:
                    pass
                kwargs[key] = value
                
        run_action(args.platform, args.action_type, kwargs)
    else:
        parser.print_help()

def run_action(platform, action_type, kwargs):
    print("=" * 60)
    print(f"{platform.upper()} {action_type.upper()} Execution")
    print("=" * 60)
    print(f"Arguments: {kwargs}")
    print("=" * 60)
    
    # Initialize Bot
    print("\n[1/3] Initializing bot...")
    try:
        BotClass, login_url = get_bot_class(platform)
        
        # Initialize with MAC platform by default
        bot = BotClass(login_url, 'MAC')
        
        # Monkeypatch _has_challenge to always return False
        bot._has_challenge = lambda: False
        
        bot.headless = False
        print("  ✓ Browser will be visible (headless mode disabled)")
        
        # Auth Management
        auth = AuthManager(platform)
        auth.load_cookies(bot)
            
        # Initialize driver
        print("  Initializing browser...")
        driver_result = bot.web_driver(login_required=False)
        
        # Check driver availability
        driver_available = hasattr(bot, 'driver') and bot.driver is not None
        
        if not driver_available:
            error_msg = "Driver not initialized"
            if isinstance(driver_result, dict):
                error_msg = driver_result.get('message', 'Unknown error')
            print(f"✗ Failed to initialize driver: {error_msg}")
            sys.exit(1)
             
        print(f"  ✓ Driver initialized (current URL: {bot.driver.current_url[:50]}...)")

        # Check login and save cookies if needed
        auth.check_and_save_login(bot)
        
    except Exception as e:
        print(f"✗ Failed to initialize bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    # Create action
    action = MockAction(platform, action_type, **kwargs)
    
    # Setup enhanced logging
    setup_enhanced_logging()
    
    # Execute
    runner = ActionRunner(bot, action)
    runner.run()
    
    print("\nBrowser is still open. Press Enter to close it (or Ctrl+C to keep it open if running in terminal)...")
    try:
        # input()
        pass
    except:
        pass

if __name__ == "__main__":
    main()
