import unittest
from unittest.mock import MagicMock, patch
import sys
from newAgent.main import main

class TestIntegration(unittest.TestCase):
    @patch('newAgent.main.ActionRunner')
    @patch('newAgent.main.AuthManager')
    @patch('newAgent.main.get_bot_class')
    @patch('newAgent.main.setup_enhanced_logging')
    def test_full_flow(self, mock_logging, mock_get_bot, MockAuthManager, MockRunner):
        # Setup mocks
        mock_bot_class = MagicMock()
        mock_bot_instance = mock_bot_class.return_value
        mock_bot_instance.web_driver.return_value = True # Driver init success
        mock_bot_instance.driver = MagicMock() # Mock driver object
        mock_get_bot.return_value = (mock_bot_class, 'http://login.url')
        
        mock_auth_instance = MockAuthManager.return_value
        
        mock_runner_instance = MockRunner.return_value
        
        # Test args
        test_args = ['main.py', 'linkedin', 'KEYWORD_SEARCH', 'keyword="test"', 'max_results=5']
        
        with patch.object(sys, 'argv', test_args):
            # Run main
            # We need to catch SystemExit because main() might not exit, but if it does with 0 it's fine.
            # In my implementation main() doesn't sys.exit(0) at the end, it just finishes.
            try:
                main()
            except SystemExit as e:
                self.assertEqual(e.code, 0)

        # Verifications
        
        # 1. Bot Initialization
        mock_get_bot.assert_called_with('linkedin')
        mock_bot_class.assert_called_with('http://login.url', 'MAC')
        mock_bot_instance.web_driver.assert_called_with(login_required=False)
        
        # 2. Auth
        MockAuthManager.assert_called_with('linkedin')
        mock_auth_instance.load_cookies.assert_called_with(mock_bot_instance)
        mock_auth_instance.check_and_save_login.assert_called_with(mock_bot_instance)
        
        # 3. Runner
        MockRunner.assert_called_once()
        # Check action args passed to runner
        call_args = MockRunner.call_args
        bot_arg = call_args[0][0]
        action_arg = call_args[0][1]
        
        self.assertEqual(bot_arg, mock_bot_instance)
        self.assertEqual(action_arg.source, 'LINKEDIN')
        self.assertEqual(action_arg.type, 'KEYWORD_SEARCH')
        self.assertEqual(action_arg.keyword, 'test')
        self.assertEqual(action_arg.maxResultsCount, 5)
        
        # 4. Execution
        mock_runner_instance.run.assert_called_once()

if __name__ == '__main__':
    unittest.main()
