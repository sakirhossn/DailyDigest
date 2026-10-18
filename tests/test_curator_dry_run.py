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
    @patch("google.genai.Client")
    def test_curate_news_with_gemini_config(self, mock_client_cls):
        """Ensure curate_news_with_gemini passes GenerateContentConfig with AFC disabled."""
        from unittest.mock import MagicMock
        from processors.curator import curate_news_with_gemini

        mock_instance = MagicMock()
        mock_client_cls.return_value = mock_instance
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "date": "18 October 2026",
            "exam_type": "ALL",
            "headline_summary": "Test summary",
            "categories": [],
            "daily_quiz": [],
            "vocabulary": [],
            "idioms": [],
            "gk_boosters": [],
        })
        mock_instance.models.generate_content.return_value = mock_response

        articles = [{"category": "General", "title": "Headline", "summary": "Body", "link": "https://example.com", "published": "2026-10-18"}]
        bulletin = curate_news_with_gemini(articles, "ALL", "fake_key", model_override="gemini-3.8-flash")

        self.assertIsNotNone(bulletin)
        mock_instance.models.generate_content.assert_called_once()
        _, kwargs = mock_instance.models.generate_content.call_args
        self.assertEqual(kwargs.get("model"), "gemini-3.8-flash")
        config = kwargs.get("config")
        self.assertIsNotNone(config)
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertTrue(config.automatic_function_calling.disable)


if __name__ == "__main__":
    unittest.main()

