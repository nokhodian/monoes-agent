import unittest
from newAgent.core.bot import get_bot_class
from newAgent.src.robot.instagram import Instagram
from newAgent.src.robot.linkedin import Linkedin
from newAgent.src.robot.x import X
from newAgent.src.robot.tiktok import Tiktok

class TestBotFactory(unittest.TestCase):
    def test_get_bot_instagram(self):
        BotClass, login_url = get_bot_class('instagram')
        self.assertEqual(BotClass, Instagram)
        self.assertIn('instagram.com', login_url)

    def test_get_bot_linkedin(self):
        BotClass, login_url = get_bot_class('linkedin')
        self.assertEqual(BotClass, Linkedin)
        self.assertIn('linkedin.com', login_url)

    def test_get_bot_x(self):
        BotClass, login_url = get_bot_class('x')
        self.assertEqual(BotClass, X)
        self.assertIn('x.com', login_url)
        
    def test_get_bot_tiktok(self):
        BotClass, login_url = get_bot_class('tiktok')
        self.assertEqual(BotClass, Tiktok)
        self.assertIn('tiktok.com', login_url)

    def test_invalid_platform(self):
        with self.assertRaises(ValueError):
            get_bot_class('invalid_platform')

    def test_case_insensitivity(self):
        BotClass, _ = get_bot_class('LiNkEdIn')
        self.assertEqual(BotClass, Linkedin)

if __name__ == '__main__':
    unittest.main()
