import unittest
from unittest.mock import MagicMock, patch
from newAgent.core.runner import ActionRunner

class TestActionRunner(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_action = MagicMock()
        self.runner = ActionRunner(self.mock_bot, self.mock_action)

    @patch('newAgent.core.runner.ActionExecutor')
    def test_run_success(self, MockExecutor):
        # Setup mock executor
        mock_executor_instance = MockExecutor.return_value
        expected_result = {'success': True, 'data': 'test'}
        mock_executor_instance.execute.return_value = expected_result
        
        result = self.runner.run()
        
        self.assertEqual(result, expected_result)
        MockExecutor.assert_called_with(self.mock_bot, self.mock_action)
        mock_executor_instance.execute.assert_called_once()

    @patch('newAgent.core.runner.ActionExecutor')
    def test_run_failure(self, MockExecutor):
        # Setup mock executor to raise exception
        mock_executor_instance = MockExecutor.return_value
        mock_executor_instance.execute.side_effect = Exception("Test Error")
        
        result = self.runner.run()
        
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
