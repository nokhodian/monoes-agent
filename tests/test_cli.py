import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
from newAgent.main import main

class TestCLI(unittest.TestCase):
    @patch('newAgent.main.run_action')
    def test_run_command_explicit(self, mock_run_action):
        test_args = ['main.py', 'run', 'linkedin', 'KEYWORD_SEARCH', 'keyword="test"']
        with patch.object(sys, 'argv', test_args):
            main()
            
        mock_run_action.assert_called_once()
        args = mock_run_action.call_args[0]
        self.assertEqual(args[0], 'linkedin')
        self.assertEqual(args[1], 'KEYWORD_SEARCH')
        self.assertEqual(args[2], {'keyword': 'test'})

    @patch('newAgent.main.run_action')
    def test_run_command_implicit(self, mock_run_action):
        # Testing "python newAgent/main.py linkedin KEYWORD_SEARCH ..."
        test_args = ['main.py', 'linkedin', 'KEYWORD_SEARCH', 'keyword="test"']
        with patch.object(sys, 'argv', test_args):
            main()
            
        mock_run_action.assert_called_once()
        args = mock_run_action.call_args[0]
        self.assertEqual(args[0], 'linkedin')
        self.assertEqual(args[1], 'KEYWORD_SEARCH')

    @patch('sys.stdout', new_callable=StringIO)
    def test_help_command(self, mock_stdout):
        test_args = ['main.py', '--help']
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit):
                main()
        
        output = mock_stdout.getvalue()
        self.assertIn('NewAgent CLI', output)

if __name__ == '__main__':
    unittest.main()
