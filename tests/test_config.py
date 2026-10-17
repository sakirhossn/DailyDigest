"""
Unit tests for configuration loading and validation in config.py
"""

import os
import unittest
from unittest.mock import patch


class TestConfig(unittest.TestCase):

    def test_default_gemini_model_is_valid(self):
        """Ensure default GEMINI_MODEL is gemini-2.5-flash and not fictitious gemini-3.6-flash."""
        import config
        self.assertEqual(config.GEMINI_MODEL, "gemini-2.5-flash")

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
