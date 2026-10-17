"""
Unit tests for 10-day revision digest idempotency and state checkpointing in revision_digest.py
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import revision_digest


class TestRevisionDigest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.log_path = self.temp_path / "revision_log.json"
        self.state_path = self.temp_path / "revision_state.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("revision_digest.dispatch_gmail")
    @patch("revision_digest.generate_pdf_bytes")
    def test_idempotent_revision_trigger(self, mock_pdf, mock_gmail):
        """Ensure running revision_digest twice on a 10-entry log only dispatches email ONCE."""
        mock_gmail.return_value = True
        mock_pdf.return_value = b"%PDF-1.4 test"

        # Create sample 10-day log
        sample_log = [
            {
                "date": f"2026-10-{i:02d}",
                "vocab_words": [{"word": f"WORD{i}", "meaning": "test"}],
                "idioms_of_the_day": [{"idiom": f"IDIOM{i}", "meaning": "test"}],
                "static_gk_boosters": [{"title": f"GK{i}", "bullets": ["b"]}],
            }
            for i in range(1, 11)
        ]
        with open(self.log_path, "w", encoding="utf-8") as fh:
            json.dump(sample_log, fh)

        with patch("revision_digest.REVISION_LOG_PATH", self.log_path), \
             patch("revision_digest.REVISION_STATE_PATH", self.state_path):

            # Initial run: should trigger email and update state
            revision_digest.main()
            self.assertEqual(mock_gmail.call_count, 1)

            # Check state was written
            self.assertTrue(self.state_path.exists())
            with open(self.state_path, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            self.assertEqual(state.get("last_revised_count"), 10)

            # Second consecutive run: should be idempotent and NOT call dispatch_gmail again
            revision_digest.main()
            self.assertEqual(mock_gmail.call_count, 1)  # count remains 1!


if __name__ == "__main__":
    unittest.main()
