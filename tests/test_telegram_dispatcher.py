"""
Unit tests for Telegram Dispatcher in dispatchers/telegram_dispatcher.py
"""

import unittest
from unittest.mock import MagicMock, patch
from dispatchers.telegram_dispatcher import _mask_token, dispatch_telegram, send_single_chunk


class TestTelegramDispatcher(unittest.TestCase):

    def test_mask_token(self):
        """Ensure token is stripped from log strings."""
        token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        error_msg = f"Failed to connect to https://api.telegram.org/bot{token}/sendMessage"
        masked = _mask_token(error_msg, token)
        self.assertNotIn(token, masked)
        self.assertIn("[MASKED_BOT_TOKEN]", masked)

    @patch("dispatchers.telegram_dispatcher.requests.post")
    def test_dispatch_multi_chat_success(self, mock_post):
        """Ensure all chunks are dispatched to all comma-separated chats."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        chunks = ["Chunk 1", "Chunk 2"]
        success = dispatch_telegram(
            chunks=chunks,
            bot_token="test_token",
            chat_id="11111,22222",
        )
        self.assertTrue(success)
        # 2 chats * 2 chunks = 4 calls
        self.assertEqual(mock_post.call_count, 4)

    @patch("dispatchers.telegram_dispatcher.requests.post")
    def test_dispatch_fails_if_any_chunk_fails(self, mock_post):
        """Ensure dispatch_telegram returns False if a chunk fails and does not mask partial failures."""
        # Chunk 1 succeeds, Chunk 2 fails
        mock_ok = MagicMock()
        mock_ok.json.return_value = {"ok": True}

        mock_fail = MagicMock()
        mock_fail.json.return_value = {"ok": False, "description": "Bad Request"}

        mock_post.side_effect = [mock_ok, mock_fail, mock_fail]  # initial try + retry

        chunks = ["Chunk 1", "Chunk 2"]
        success = dispatch_telegram(
            chunks=chunks,
            bot_token="test_token",
            chat_id="11111",
        )
        self.assertFalse(success)


if __name__ == "__main__":
    unittest.main()
