"""
Unit tests for RSS Ingestion and deduplication in sources/rss_fetcher.py
"""

import unittest
from sources.rss_fetcher import are_titles_similar, clean_html, deduplicate_articles


class TestRSSFetcher(unittest.TestCase):

    def test_clean_html(self):
        """Ensure clean_html strips script/style tags and extra whitespace."""
        raw = "<p>India launches <b>new satellite</b>.<style>body{color:red}</style><script>alert(1)</script></p>"
        cleaned = clean_html(raw)
        self.assertEqual(cleaned, "India launches new satellite.")

    def test_are_titles_similar(self):
        """Ensure token Jaccard similarity detects near-identical headlines."""
        t1 = "ISRO successfully launches PSLV-C58 satellite mission"
        t2 = "ISRO launches PSLV-C58 satellite mission successfully into orbit"
        t3 = "Reserve Bank of India keeps repo rate unchanged at 6.5%"

        self.assertTrue(are_titles_similar(t1, t2))
        self.assertFalse(are_titles_similar(t1, t3))

    def test_deduplicate_articles(self):
        """Ensure deduplicate_articles filters out exact URLs and similar titles."""
        articles = [
            {"title": "RBI monetary policy committee holds repo rate", "link": "https://example.com/rbi1"},
            {"title": "RBI monetary policy committee holds repo rate unchanged", "link": "https://example.com/rbi2"},
            {"title": "Different story on national highways expansion", "link": "https://example.com/rbi1"},  # duplicate link
            {"title": "Different story on national highways expansion", "link": "https://example.com/nh1"},
        ]
        deduped = deduplicate_articles(articles)
        # Should keep only 2 unique stories
        self.assertEqual(len(deduped), 2)


if __name__ == "__main__":
    unittest.main()
