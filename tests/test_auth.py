import unittest
from unittest.mock import MagicMock, patch
from newAgent.core.auth import AuthManager

class TestAuthManager(unittest.TestCase):
    def setUp(self):
        # Patch the SessionStore to avoid actual DB operations
        self.patcher = patch('newAgent.core.auth.SessionStore')
        self.MockSessionStore = self.patcher.start()
        self.mock_store_instance = self.MockSessionStore.return_value
        
        self.auth = AuthManager('linkedin')
        self.mock_bot = MagicMock()
        self.mock_bot.cookies = []
        self.mock_bot.username = None
        self.mock_bot.profile_pic = None

    def tearDown(self):
        self.patcher.stop()

    def test_load_cookies_success(self):
        # Setup mock return value for latest_cookies
        # Format: (cookies, username, profile_pic)
        mock_cookies = [{'name': 'li_at', 'value': '123'}]
        self.mock_store_instance.latest_cookies.return_value = (mock_cookies, 'testuser', 'pic.jpg')
        
        result = self.auth.load_cookies(self.mock_bot)
        
        self.assertTrue(result)
        self.assertEqual(self.mock_bot.cookies, mock_cookies)
        self.assertEqual(self.mock_bot.username, 'testuser')
        self.assertEqual(self.mock_bot.profile_pic, 'pic.jpg')

    def test_load_cookies_none(self):
        self.mock_store_instance.latest_cookies.return_value = None
        
        result = self.auth.load_cookies(self.mock_bot)
        
        self.assertFalse(result)
        self.assertEqual(self.mock_bot.cookies, [])

    @patch('newAgent.core.auth.datetime')
    def test_save_cookies(self, mock_datetime):
        # Mock datetime to have stable expiry
        mock_datetime.now.return_value.strftime.return_value = '2025-01-01'
        
        self.mock_bot.driver.get_cookies.return_value = [{'name': 'cookie', 'value': '123'}]
        self.mock_bot.username = 'saved_user'
        
        self.auth.save_cookies(self.mock_bot)
        
        # Verify insert_into_crawler_session was called
        self.mock_store_instance.insert_into_crawler_session.assert_called_once()
        call_args = self.mock_store_instance.insert_into_crawler_session.call_args[1]
        self.assertEqual(call_args['username'], 'saved_user')
        self.assertEqual(call_args['social'], 'LINKEDIN')
        self.assertEqual(call_args['cookies'], [{'name': 'cookie', 'value': '123'}])

if __name__ == '__main__':
    unittest.main()
