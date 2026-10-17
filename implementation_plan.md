# DailyDigest Engineering Audit & Remediation Implementation Plan

**Repository:** `https://github.com/sakirhossn/DailyDigest`  
**Owner:** `sakirhossn`  
**Target Branch for Remediation:** `remediation/audit-fixes` (branched from `main` at `9ba951f`)  
**Date:** 2026-10-18  

---

## 1. Executive Summary and Project Architecture

### 1.1 Executive Summary
DailyDigest is an automated, Python-based current-affairs aggregator and exam preparation agent designed for aspirants preparing for competitive Indian government and banking examinations (UPSC, SSC, Banking, RRB, and State PSCs). The system executes daily scheduled data extraction from national and financial news RSS feeds, performs text normalization and deduplication, generates structured educational bulletins and Multiple Choice Questions (MCQs) using Google Gemini generative AI (with an algorithmic heuristic fallback), and formats outputs into Telegram Markdown messages and HTML email newsletters. It further archives digests into a GitHub Pages web portal and generates 10-day revision compilations with PDF generation and vocabulary tracking.

This audit evaluates the system across architecture, correctness, data security, network resilience, HTML/injection safety, multi-recipient dispatching, idempotency, and automated CI/CD deployment pipelines.

### 1.2 System Architecture Diagram
```
                      +-----------------------------+
                      |   RSS News Feeds (11 feeds) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | sources/rss_fetcher.py      |
                      | - Concurrent HTTP fetches   |
                      | - BeautifulSoup HTML strip  |
                      | - Exact & Fuzzy title dedup |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | processors/curator.py       |
                      | - Gemini Generative AI      |
                      | - Heuristic fallback engine |
                      | - MCQ generator & validator |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | processors/formatter.py     |
                      | - HTML Email builder        |
                      | - Telegram chunking (4096B) |
                      +-------+--------------+------+
                              |              |
           +------------------+              +------------------+
           v                                                    v
+-------------------------+                          +-------------------------+
| dispatchers/telegram    |                          | dispatchers/gmail       |
| - Bot API sendMessage   |                          | - SMTP SSL (smtp.gmail) |
| - Markdown -> text retry|                          | - Multi-recipient BCC   |
+-------------------------+                          +-------------------------+
           |                                                    |
           +------------------+              +------------------+
                              |              |
                              v              v
                      +-----------------------------+
                      | Archive & Revision          |
                      | - docs/archive/*.html       |
                      | - revision_digest.py        |
                      | - xhtml2pdf PDF generation  |
                      | - GitHub Pages deployment   |
                      +-----------------------------+
```

---

## 2. Repository Structure and Important Execution Paths

### 2.1 File Structure
- `config.py`: Environment variable ingestion via `python-dotenv`, model configurations, feed mappings, and exam constants.
- `main.py`: CLI driver supporting `--exam`, `--channel`, `--save-html`, and `--dry-run`.
- `scheduler.py`: Local background loop executing `schedule.every().day.at()`.
- `revision_digest.py`: Milestone runner triggering every 10 days; generates 50-MCQ quizzes and PDF revisions.
- `sources/rss_fetcher.py`: Multithreaded RSS parsing (`feedparser` / `concurrent.futures`), HTML tag stripping, title similarity deduplication.
- `processors/curator.py`: Gemini client interaction (`google-genai`), JSON schema extraction, exam mapping, static GK linking, and heuristic backup.
- `processors/formatter.py`: HTML template builder, CSS injection, responsive styling, Telegram chunking (< 4000 chars).
- `dispatchers/telegram_dispatcher.py`: Telegram Bot API wrapper with connection tests and markdown fallback.
- `dispatchers/gmail_dispatcher.py`: Python `smtplib` wrapper for MIME multipart email dispatch.
- `docs/`: Web archive frontend (`index.html`) and historical archive (`docs/archive/`).
- `.github/workflows/daily_digest.yml`: GitHub Actions workflow on daily cron (`00:47 UTC`), running pipeline, committing archive, and deploying Pages.

### 2.2 Critical Execution Paths
1. **Daily Scheduled Run (CI/CD):** `.github/workflows/daily_digest.yml` executes `main.py --channel both --exam all --save-html daily_digest.html` -> git commits archive -> triggers `revision_digest.py` -> publishes GitHub Pages.
2. **Local Daemon Run:** `python scheduler.py` monitors system clock and fires `run_agent()`.
3. **Manual CLI Dispatch / Dry Run:** `python main.py --dry-run --channel preview`.

---

## 3. Audit Scope and Out-of-Scope Items

### 3.1 In-Scope Items
- Full static analysis and runtime verification of all 8 core Python modules (`config.py`, `main.py`, `scheduler.py`, `revision_digest.py`, `sources/rss_fetcher.py`, `processors/curator.py`, `processors/formatter.py`, `dispatchers/*.py`).
- Security assessment: credential handling, injection vulnerabilities (HTML/XSS, command injection), path traversal, and untrusted feed content processing.
- Error handling, timeouts, retries, and network failure resilience.
- Data persistence, idempotency, side-effects of preview/dry-run modes.
- Multi-recipient dispatching for Telegram and Gmail.
- GitHub Actions workflow analysis: permissions, secret handling, concurrency, and race conditions.
- Test harness creation: unit, mock, and regression test suites.

### 3.2 Out-of-Scope Items
- Sending real live emails or Telegram messages to real end-users during testing.
- Overwriting historical archived HTML files (`docs/archive/*.html`) or modifying user `.env` files.
- Modifying remote GitHub repository settings or creating actual production secrets.

---

## 4. Workstreams: Security, Correctness, Reliability, Maintainability & Deployment

1. **Security Workstream:**
   - XSS / HTML Injection prevention: ensure RSS titles, article summaries, external links, and AI text are strictly sanitized using `html.escape()`.
   - Secret hygiene: ensure tokens, app passwords, and API keys are never printed in loggers, stack traces, or artifacts.
2. **Correctness Workstream:**
   - Model name validation: resolve discrepancy where `gemini-3.6-flash` is configured but does not exist in the official API roster.
   - CLI parameter handling and channel dispatching: ensure `--dry-run` and `--channel preview` never mutate `used_content.json` or `revision_log.json`.
   - Telegram multi-recipient support: expand `telegram_dispatcher.py` to support comma-separated chat IDs just like `gmail_dispatcher.py`.
3. **Reliability & Idempotency Workstream:**
   - Revision digest trigger logic: fix `total % REVISION_EVERY_N_DAYS != 0` to prevent duplicate emails and handle missed milestones via persistent tracking.
   - Network resilience: verify socket timeouts, HTTP status checks, and exponential backoff.
4. **Maintainability Workstream:**
   - Clean architecture, code duplication removal, typing improvements, and unit test suite creation.
5. **Deployment Workstream:**
   - Align schedule times between `daily_digest.yml` (`00:47 UTC` = `06:17 AM IST`), `config.py` (`09:37`), and documentation.

---

## 5. Proposed Test Strategy and Test-Data Requirements

### 5.1 Test Suites
- **Unit Tests (`tests/test_units.py`):**
  - RSS parser edge cases: malformed XML, missing dates, dirty HTML titles, empty categories.
  - Deduplication: title fuzzy-matching, exact URLs, cross-category collisions.
  - Formatter & Escaping: verifying `html.escape()` protects against `<script>`, `onerror`, and malformed URLs.
  - Telegram chunking: long inputs (> 4096 characters), tag preservation across boundaries.
- **Mock Integration Tests (`tests/test_integration.py`):**
  - Mocked Gemini responses (valid JSON, invalid JSON, rate limit 429, timeout).
  - Mocked SMTP server: multi-recipient delivery verification.
  - Mocked Telegram Bot API: simulated markdown parsing failure and plain-text fallback.
  - Dry-run assertion: verifying no files in `docs/archive/` are modified when `--dry-run` is active.
- **Regression Tests (`tests/test_regression.py`):**
  - 10-day revision calculation and idempotency: running twice does not send duplicate revision emails.

---

## 6. The Five Review Commands and Their Respective Purposes

1. `/gsd-code-review`: Systematic code review evaluating correctness, maintainability, architectural design, and regression risks.
2. `/ponytail`: Evaluates codebase against the Ponytail minimalist design philosophy (YAGNI, stdlib-first, native platforms, eliminating speculative complexity).
3. `/ponytail-gain`: Displays measured benchmark scoreboard for code efficiency, footprint, and maintenance overhead.
4. `/ponytail-audit`: Repository-wide audit for dead code, unneeded dependencies, single-implementation abstractions, and bloat.
5. `/ponytail-review`: Line-by-line review of modified files and diffs hunting over-engineering and extraneous code.

---

## 7. Expected Output Artifacts

1. `implementation_plan.md`: Comprehensive engineering roadmap (this document).
2. `audit_report.md`: Complete audit findings categorized with unique IDs (`DD-SEC-xxx`, `DD-COR-xxx`, `DD-REL-xxx`, `DD-DEP-xxx`).
3. `test_report.md`: Detailed test execution report detailing all test cases, mocks, assertions, and outcomes.
4. `security_report.md`: Threat model, credential audit, injection audit, and dependency vulnerability assessment.
5. `remediation_summary.md`: Summary of code modifications made in branch `remediation/audit-fixes`.

---

## 8. Priorities, Dependencies, Completion Criteria, and Rollback Strategy

### 8.1 Priorities
- **P0 (Critical Security & Correctness):**
  - Fix HTML escaping in `formatter.py` (prevent XSS/HTML injection).
  - Fix Gemini model name in `config.py` & `curator.py`.
  - Fix state mutation side-effect on `--dry-run` / `preview`.
- **P1 (Reliability & Multi-User):**
  - Fix 10-day revision digest idempotency.
  - Support multi-chat Telegram dispatching (`TELEGRAM_CHAT_ID` comma-separated).
- **P2 (Maintainability & Alignment):**
  - Align scheduler documentation and GitHub Actions cron schedule.
  - Remove redundant dependencies and dead code.

### 8.2 Completion Criteria
- All P0 and P1 issues remediated in `remediation/audit-fixes`.
- 100% pass rate across all automated unit, mock, and regression test suites.
- Clean working directory with no untracked artifacts or modified historical files.
- Final review conducted using all 5 commands with zero unaddressed regressions.

### 8.3 Rollback Strategy
- All modifications are confined to the dedicated branch `remediation/audit-fixes`.
- If any remediation introduces an unintended regression, `git checkout main` or `git revert` provides immediate restoration.
- `main` remains pristine throughout the audit and remediation process.

---

## 9. Risks That Need Manual Review or External Credentials

1. **Live Gemini API Quota & Billing:** Verification of real API calls requires active `GEMINI_API_KEY` with adequate quota; tests will mock API calls to avoid draining user credits or failing in offline environments.
2. **Gmail SMTP App Password:** Real email transmission requires a valid 16-character Google App Password with 2-Step Verification enabled; tests use mocked `smtplib.SMTP_SSL`.
3. **Telegram Bot Webhook Conflicts:** Sending real messages requires a valid bot token and chat ID; tests use mocked HTTP endpoints.

---

## 10. Verification Matrix

| Identified Risk / Defect | Severity | Proposed Remediation | Verification Method |
| :--- | :--- | :--- | :--- |
| **Non-existent Gemini Model** (`gemini-3.6-flash`) | High | Change default in `config.py` and `curator.py` to `gemini-2.5-flash` (or valid 3.x if confirmed supported) with robust fallback. | Unit test verifying model name resolution and mocked API invocation. |
| **HTML Injection / XSS in Formatter** | High | Use `html.escape()` for titles, descriptions, links, and AI text in `formatter.py`. | Injection unit test asserting `<script>` and malicious HTML tags are escaped. |
| **Dry-Run Mutates Persistent Storage** | Medium | Pass `dry_run` flag to `curator.py` and guard `save_used_content()` and `append_revision_log()`. | Integration test verifying files on disk are identical before and after `--dry-run`. |
| **Revision Digest Non-Idempotency** | Medium | Track last processed revision milestone in persistent JSON log (`docs/archive/revision_state.json`). | Test running `revision_digest.py` twice consecutively on 10th-day state. |
| **Telegram Single-Recipient Limit** | Medium | Support comma-separated IDs in `TELEGRAM_CHAT_ID` and loop over recipients in `telegram_dispatcher.py`. | Unit test verifying multi-chat dispatch and error aggregation. |
| **Time Discrepancy (Actions vs Config)** | Low | Harmonize cron schedule in workflow and `config.py` with clear documentation. | Inspection and config test. |

---
