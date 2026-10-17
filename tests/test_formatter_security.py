"""
Unit tests for security, XSS, and HTML escaping in processors/formatter.py
"""

import unittest
from processors.formatter import (
    _safe_url,
    format_gmail_html,
    format_revision_digest_html,
    format_revision_digest_pdf_html,
)


class TestFormatterSecurity(unittest.TestCase):

    def test_safe_url_validation(self):
        """Ensure _safe_url allows http/https and blocks dangerous schemes like javascript:."""
        self.assertEqual(_safe_url("https://example.com/news"), "https://example.com/news")
        self.assertEqual(_safe_url("http://example.com/path?q=1&b=2"), "http://example.com/path?q=1&amp;b=2")
        self.assertEqual(_safe_url("javascript:alert(1)"), "")
        self.assertEqual(_safe_url("data:text/html,<script>"), "")
        self.assertEqual(_safe_url("vbscript:msgbox(1)"), "")
        self.assertEqual(_safe_url(""), "")

    def test_gmail_html_escapes_xss_payloads(self):
        """Ensure malicious HTML/script tags in titles, summaries, and links are escaped."""
        malicious_bulletin = {
            "date": "18 October 2026",
            "exam_type": "UPSC",
            "headline_summary": "<script>alert('headline_xss')</script>",
            "categories": [
                {
                    "category_name": "<b onmouseover=alert('cat')>Polity</b>",
                    "items": [
                        {
                            "title": "<img src=x onerror=alert('title_xss')>",
                            "exam_tag": "<script>tag</script>",
                            "summary_bullets": [
                                "<script>alert('bullet_xss')</script>",
                                "Normal bullet text",
                            ],
                            "static_gk_or_deep_dive": "<iframe src='evil.com'></iframe>",
                            "link": "javascript:alert('link_xss')",
                        }
                    ],
                }
            ],
            "vocab_words": [
                {
                    "word": "<script>vocab</script>",
                    "part_of_speech": "Noun",
                    "meaning": "<b>dangerous meaning</b>",
                    "synonyms": ["<script>syn</script>"],
                    "antonyms": ["<script>ant</script>"],
                    "example_sentence": "<img src=x onerror=alert('vocab_ex')>",
                }
            ],
            "idioms_of_the_day": [
                {
                    "idiom": "<script>idiom</script>",
                    "meaning": "<script>meaning</script>",
                    "example_sentence": "<script>ex</script>",
                }
            ],
            "static_gk_boosters": [
                {
                    "title": "<script>booster</script>",
                    "bullets": ["<script>bullet</script>"],
                }
            ],
            "daily_quiz": [
                {
                    "question": "<script>quiz_q</script>",
                    "options": ["A) <script>optA</script>", "B) <script>optB</script>"],
                    "correct": "A",
                    "explanation": "<script>quiz_exp</script>",
                }
            ],
        }

        output_html = format_gmail_html(malicious_bulletin)

        # Assert no raw unescaped script or iframe tags exist in the generated HTML
        self.assertNotIn("<script>", output_html)
        self.assertNotIn("</script>", output_html)
        self.assertNotIn("<iframe", output_html)
        self.assertNotIn("javascript:alert", output_html)

        # Assert properly escaped representations exist
        self.assertIn("&lt;script&gt;alert(&#x27;headline_xss&#x27;)&lt;/script&gt;", output_html)
        self.assertIn("&lt;img src=x onerror=alert(&#x27;title_xss&#x27;)&gt;", output_html)
        self.assertIn("&lt;iframe src=&#x27;evil.com&#x27;&gt;&lt;/iframe&gt;", output_html)

    def test_revision_digest_html_escapes_xss(self):
        """Ensure revision digest HTML templates escape dangerous inputs."""
        malicious_entries = [
            {
                "date": "<script>alert('date')</script>",
                "vocab_words": [
                    {
                        "word": "<script>V</script>",
                        "part_of_speech": "Noun",
                        "meaning": "<script>M</script>",
                    }
                ],
                "idioms_of_the_day": [
                    {
                        "idiom": "<script>I</script>",
                        "meaning": "<script>IM</script>",
                    }
                ],
                "static_gk_boosters": [
                    {
                        "title": "<script>T</script>",
                        "bullets": ["<script>B</script>"],
                    }
                ],
            }
        ]

        html_out = format_revision_digest_html(malicious_entries, "<script>start</script>", "end")
        self.assertNotIn("<script>", html_out)
        self.assertIn("&lt;script&gt;alert(&#x27;date&#x27;)&lt;/script&gt;", html_out)

        pdf_html_out = format_revision_digest_pdf_html(malicious_entries, "<script>start</script>", "end")
        self.assertNotIn("<script>", pdf_html_out)


if __name__ == "__main__":
    unittest.main()
