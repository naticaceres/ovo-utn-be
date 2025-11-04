import unittest
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
import json

# Import the functions to test
from lib.chat import chat as chat_module

class TestChatUtils(unittest.TestCase):

    def test_extract_final_scores_basic(self):
        txt = "ANÁLISIS FINAL\nSome text\nfinal_scores: apt1: 0.5, apt2: 0.8, apt3: 0.0"
        result = chat_module.extract_final_scores_from_response(txt)
        self.assertIsInstance(result, dict)
        self.assertAlmostEqual(result.get('apt1'), 0.5)
        self.assertAlmostEqual(result.get('apt2'), 0.8)
        self.assertAlmostEqual(result.get('apt3'), 0.0)

    def test_extract_final_scores_missing(self):
        txt = "No final scores here"
        result = chat_module.extract_final_scores_from_response(txt)
        self.assertIsNone(result)

    def test_clean_chatbot_response_removes_final_scores(self):
        txt = "Some answer text\nfinal_scores: apt1: 0.5, apt2: 0.2"
        cleaned = chat_module.clean_chatbot_response(txt)
        self.assertNotIn("final_scores", cleaned.lower())
        self.assertTrue(cleaned.strip().endswith("text"))

    def test_build_dynamic_master_prompt(self):
        sample = ["Apt1", "Apt2", "Apt3", "Apt4", "Apt5", "Extra"]
        prompt = chat_module.build_dynamic_master_prompt(sample)
        self.assertIn("Apt1", prompt)
        self.assertIn("Apt5", prompt)
        # Now includes all provided aptitudes (dynamic count)
        self.assertIn("Extra", prompt)

    def _make_client_error(self):
        error_response = {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'cond failed'}}
        return ClientError(error_response, 'UpdateItem')

    @patch('lib.chat.chat.handle_quota_check')
    def test_check_quotas_success(self, mock_handle_quota):
        # simulate both calls succeed (handle_quota_check called twice without raising)
        mock_handle_quota.return_value = None
        quota_table = MagicMock()
        result = chat_module.check_quotas(quota_table, 'user123', '2025-01-01')
        self.assertIsNone(result)

    @patch('lib.chat.chat.handle_quota_check')
    def test_check_quotas_user_exceeded_reverts_global(self, mock_handle_quota):
        # first call (global) succeeds, second call raises ClientError
        def side_effect(table, uid, date, limit):
            if uid == chat_module.GLOBAL_USER_ID:
                return None
            raise self._make_client_error()
        mock_handle_quota.side_effect = side_effect
        quota_table = MagicMock()
        result = chat_module.check_quotas(quota_table, 'user123', '2025-01-01')
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('statusCode'), 429)

    @patch('lib.chat.chat.handle_quota_check')
    def test_check_quotas_global_exceeded(self, mock_handle_quota):
        # first call raises ClientError for global
        mock_handle_quota.side_effect = self._make_client_error()
        quota_table = MagicMock()
        result = chat_module.check_quotas(quota_table, 'user123', '2025-01-01')
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('statusCode'), 429)

if __name__ == '__main__':
    unittest.main()