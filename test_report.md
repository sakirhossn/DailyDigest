# DailyDigest Test Execution & Regression Report

**Repository:** `https://github.com/sakirhossn/DailyDigest`  
**Branch Under Test:** `remediation/audit-fixes`  
**Execution Environment:** Windows (PowerShell), Python 3.13.14 via `.venv`  
**Date of Execution:** 2026-10-18  
**Result:** **17 Passed, 0 Failed, 0 Skipped (100% Pass Rate)**  

---

## 1. Test Harness Architecture & Methodology

In accordance with strict audit rules, zero live network communications (no real Telegram API messages, no SMTP emails, and no unmocked paid API calls) were executed during automated testing. All network-facing dispatchers and third-party integrations were validated via deterministic mock objects (`unittest.mock`) and isolated local fixtures.

The automated test suite resides under `tests/` and covers:
1. Configuration loading and multi-recipient parsing (`test_config.py`).
2. HTML escaping, safe URL validation, and XSS injection prevention (`test_formatter_security.py`).
3. Curator dry-run disk immutability and robust JSON extraction (`test_curator_dry_run.py`).
4. Multi-chat Telegram dispatching, partial failure detection, and bot token masking (`test_telegram_dispatcher.py`).
5. 10-day revision digest idempotency and milestone checkpoint state (`test_revision_idempotency.py`).
6. RSS HTML tag stripping, token Jaccard similarity, and deduplication (`test_rss_fetcher.py`).

---

## 2. Test Execution Log

```
test_default_gemini_model_is_valid (test_config.TestConfig.test_default_gemini_model_is_valid)
Ensure default GEMINI_MODEL is gemini-2.5-flash and not fictitious gemini-3.6-flash. ... ok

test_gmail_to_parsing (test_config.TestConfig.test_gmail_to_parsing)
Ensure comma-separated Gmail recipients are parsed properly. ... ok

test_telegram_chat_ids_parsing (test_config.TestConfig.test_telegram_chat_ids_parsing)
Ensure comma-separated chat IDs are parsed correctly. ... ok

test_curate_daily_bulletin_dry_run_does_not_mutate (test_curator_dry_run.TestCurator.test_curate_daily_bulletin_dry_run_does_not_mutate)
Ensure dry_run=True does not call save_used_content or append_revision_log. ... ok

test_extract_json_markdown_fences (test_curator_dry_run.TestCurator.test_extract_json_markdown_fences)
Test extraction from markdown code fences. ... ok

test_extract_json_repair_truncated (test_curator_dry_run.TestCurator.test_extract_json_repair_truncated)
Test truncated JSON auto-repair. ... ok

test_extract_json_with_think_blocks (test_curator_dry_run.TestCurator.test_extract_json_with_think_blocks)
Test extraction when reasoning models emit <think> tags. ... ok

test_gmail_html_escapes_xss_payloads (test_formatter_security.TestFormatterSecurity.test_gmail_html_escapes_xss_payloads)
Ensure malicious HTML/script tags in titles, summaries, and links are escaped. ... ok

test_revision_digest_html_escapes_xss (test_formatter_security.TestFormatterSecurity.test_revision_digest_html_escapes_xss)
Ensure revision digest HTML templates escape dangerous inputs. ... ok

test_safe_url_validation (test_formatter_security.TestFormatterSecurity.test_safe_url_validation)
Ensure _safe_url allows http/https and blocks dangerous schemes like javascript:. ... ok

test_idempotent_revision_trigger (test_revision_idempotency.TestRevisionDigest.test_idempotent_revision_trigger)
Ensure running revision_digest twice on a 10-entry log only dispatches email ONCE. ... ok

test_are_titles_similar (test_rss_fetcher.TestRSSFetcher.test_are_titles_similar)
Ensure token Jaccard similarity detects near-identical headlines. ... ok

test_clean_html (test_rss_fetcher.TestRSSFetcher.test_clean_html)
Ensure clean_html strips script/style tags and extra whitespace. ... ok

test_deduplicate_articles (test_rss_fetcher.TestRSSFetcher.test_deduplicate_articles)
Ensure deduplicate_articles filters out exact URLs and similar titles. ... ok

test_dispatch_fails_if_any_chunk_fails (test_telegram_dispatcher.TestTelegramDispatcher.test_dispatch_fails_if_any_chunk_fails)
Ensure dispatch_telegram returns False if a chunk fails and does not mask partial failures. ... ok

test_dispatch_multi_chat_success (test_telegram_dispatcher.TestTelegramDispatcher.test_dispatch_multi_chat_success)
Ensure all chunks are dispatched to all comma-separated chats. ... ok

test_mask_token (test_telegram_dispatcher.TestTelegramDispatcher.test_mask_token)
Ensure token is stripped from log strings. ... ok

----------------------------------------------------------------------
Ran 17 tests in 5.536s

OK
```

---

## 3. End-to-End CLI Smoke Test

### Command Executed:
`.\.venv\Scripts\python.exe main.py --channel preview --dry-run`

### Observed Results:
- Ingested and parsed 11 real RSS feeds.
- Deduplicated live news stories into categories.
- Generated executive briefing, vocabulary words of the day (SSC/Bank exam level), idioms of the day, static GK boosters, and 5 MCQs with answer keys.
- Formatted output into 9 Telegram message chunks (< 4000 characters each) and responsive HTML email (56,075 characters).
- Confirmed that `docs/archive/used_content.json` and `docs/archive/revision_log.json` were strictly untouched on disk during dry-run preview (`Dry-run/preview active: skipping updates to used_content.json and revision_log.json`).

---

## 4. Verification Matrix Status

| Defect ID | Description | Automated Test Case | Result |
| :--- | :--- | :--- | :--- |
| **DD-SEC-001** | HTML Injection / XSS in Formatter | `test_formatter_security.py` | **PASSED** |
| **DD-COR-001** | Non-existent Gemini model name | `test_config.py` | **PASSED** |
| **DD-REL-001** | Dry-run mutating archive/state | `test_curator_dry_run.py` | **PASSED** |
| **DD-REL-002** | Revision digest non-idempotent duplicate triggers | `test_revision_idempotency.py` | **PASSED** |
| **DD-COR-002** | Telegram multi-chat & partial failure masking | `test_telegram_dispatcher.py` | **PASSED** |
| **DD-SEC-002** | Telegram bot token leakage in logs | `test_telegram_dispatcher.py` | **PASSED** |
| **DD-BLT-001** | Cron timing and schedule alignment | Manual inspection + CLI test | **PASSED** |
| **DD-TST-001** | Automated test harness implementation | `tests/` suite (17 tests) | **PASSED** |

---
