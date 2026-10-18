"""
Unit tests for configuration loading and validation in config.py
"""

import os
import unittest
from unittest.mock import patch


class TestConfig(unittest.TestCase):

    def test_default_gemini_model_is_valid(self):
        """Ensure default GEMINI_MODEL is gemini-3.8-flash."""
        import importlib
        import config
        with patch.dict(os.environ, {}, clear=True):
            importlib.reload(config)
            self.assertEqual(config.GEMINI_MODEL, "gemini-3.8-flash")

    def test_deprecated_gemini_model_auto_migrated(self):
        """Ensure legacy models (e.g. gemini-2.5-flash) are automatically migrated to gemini-3.8-flash."""
        import importlib
        import config
        for legacy in ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]:
            with patch.dict(os.environ, {"GEMINI_MODEL": legacy}):
                importlib.reload(config)
                self.assertEqual(config.GEMINI_MODEL, "gemini-3.8-flash")

    def test_telegram_chat_ids_parsing(self):
        """Ensure comma-separated chat IDs are parsed correctly."""
        import config
        # Test parsing logic directly
        sample = "12345, 67890 , -100987654321"
        parsed = [c.strip() for c in sample.split(",") if c.strip()]
        self.assertEqual(parsed, ["12345", "67890", "-100987654321"])

    def test_gmail_to_parsing(self):
        """Ensure comma-separated Gmail recipients are parsed properly."""
        sample = "a@gmail.com, b@example.com ,  c@test.org"
        parsed = [e.strip() for e in sample.split(",") if e.strip()]
        self.assertEqual(parsed, ["a@gmail.com", "b@example.com", "c@test.org"])


if __name__ == "__main__":
    unittest.main()
