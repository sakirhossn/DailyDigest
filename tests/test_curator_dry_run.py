"""
Unit tests for curator dry-run state isolation and JSON parsing in processors/curator.py
"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from processors.curator import _extract_json, curate_daily_bulletin


class TestCurator(unittest.TestCase):

    def test_extract_json_markdown_fences(self):
        """Test extraction from markdown code fences."""
        raw = """Here is today's current affairs:
```json
{
  "date": "18 October 2026",
  "headline_summary": "Top summary"
}
```
Hope this helps!"""
        extracted = _extract_json(raw)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("date"), "18 October 2026")

    def test_extract_json_with_think_blocks(self):
        """Test extraction when reasoning models emit <think> tags."""
        raw = """<think>
Evaluating syllabus relevance for SSC CGL and UPSC GS-2...
</think>
{
  "date": "18 October 2026",
  "exam_type": "ALL"
}"""
        extracted = _extract_json(raw)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("date"), "18 October 2026")

    def test_extract_json_repair_truncated(self):
        """Test truncated JSON auto-repair."""
        raw = '{"date": "18 October 2026", "categories": [{"category_name": "Economy"'
        extracted = _extract_json(raw)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.get("date"), "18 October 2026")

    @patch("processors.curator.save_used_content")
    @patch("processors.curator.append_revision_log")
    def test_curate_daily_bulletin_dry_run_does_not_mutate(self, mock_append, mock_save):
        """Ensure dry_run=True does not call save_used_content or append_revision_log."""
        sample_articles = [
            {
                "category": "National & Governance",
                "title": "Government launches new national educational initiative for youth",
                "summary": "The initiative aims to build digital infrastructure and support competitive exam preparation.",
                "link": "https://example.com/edu",
                "published": "2026-10-18",
            }
        ]

        bulletin = curate_daily_bulletin(sample_articles, exam_type="ALL", api_key="", dry_run=True)
        self.assertIsNotNone(bulletin)
        mock_save.assert_not_called()
        mock_append.assert_not_called()


if __name__ == "__main__":
    unittest.main()
