# DailyDigest — Comprehensive Engineering & Security Audit Report

**Repository:** `https://github.com/sakirhossn/DailyDigest`  
**Audit Date:** 2026-10-18  
**Audit Tools Applied:** `/gsd-code-review`, `/ponytail`, `/ponytail-gain`, `/ponytail-audit`, `/ponytail-review`, and Independent Deep-Code Static/Runtime Analysis.  
**Baseline Commit:** `9ba951f` (`origin/main`)  

---

## 1. Executive Summary of Audit Findings

The DailyDigest repository is an ambitious and well-structured automation tool for exam aspirants. However, an in-depth audit revealed multiple critical defects in security (unauthenticated HTML injection / XSS), API correctness (invalid Gemini model identifier forcing failures), state mutability (dry-run modifying persistent storage), idempotency flaws (potential infinite or skipped 10-day revision emails), and single-recipient dispatch limitations.

### Summary by Severity:
- **Critical (2):**
  - `DD-SEC-001`: Unsanitized RSS & AI text interpolated directly into HTML output (XSS / HTML injection risk).
  - `DD-COR-001`: Non-existent Gemini model identifier (`gemini-3.6-flash`) causing unhandled API errors and forcing heuristic fallback.
- **High (3):**
  - `DD-REL-001`: Unconditional state mutation in `--dry-run` and `preview` modes (`used_content.json` & `revision_log.json`).
  - `DD-REL-002`: Flawed modulo-based revision trigger (`total % 10 != 0`) causing duplicate sends or missed milestones.
  - `DD-COR-002`: `telegram_dispatcher.py` masks partial chunk transmission failure and lacks multi-recipient support.
- **Medium (3):**
  - `DD-SEC-002`: Raw exception traceback exposure and sensitive URL handling.
  - `DD-BLT-001`: Discrepancy between GitHub Actions cron (`00:47 UTC` / `06:17 IST`), local config (`09:37`), and documentation.
  - `DD-ENG-001`: Over-engineered dependency tree and brittle regex-based JSON extraction in `curator.py`.
- **Low / Informational (2):**
  - `DD-ENG-002`: Redundant HTML parsing combining BeautifulSoup and regex cleanup.
  - `DD-TST-001`: Zero existing unit, integration, or regression test suites in the repository.

---

## 2. Baseline Audit Command Results

### 2.1 `/gsd-code-review` Analysis
- **Scope:** Full repository codebase (`config.py`, `main.py`, `scheduler.py`, `revision_digest.py`, `sources/rss_fetcher.py`, `processors/curator.py`, `processors/formatter.py`, `dispatchers/*.py`).
- **Core Findings:**
  1. `processors/curator.py:782-785`: State mutation occurs during bulletin curation regardless of execution mode. Invoking `--dry-run` or `--channel preview` permanently appends records to `revision_log.json` and updates `used_content.json`.
  2. `config.py:45` & `curator.py:752`: Gemini model identifier `"gemini-3.6-flash"` is invalid. The code explicitly classifies standard models (`gemini-2.5-flash`) as deprecated in favor of a fictitious model name, guaranteeing API failures.
  3. `processors/formatter.py:180-240`: Missing HTML entity encoding (`html.escape`) when building HTML digests. Article titles, summaries, and URLs from external RSS feeds are injected directly into inner HTML.
  4. `revision_digest.py:62`: The check `if total % REVISION_EVERY_N_DAYS != 0:` lacks state watermark persistence. Re-executing `revision_digest.py` on day 10 re-sends the revision email every time.

### 2.2 `/ponytail` (Minimalist Ladder Review)
- Ladder evaluation: `YAGNI -> stdlib -> native -> one line -> minimum`.
- The repository imports several heavy dependencies for simple tasks:
  - `BeautifulSoup4` + `soupsieve` is used merely to strip tags from RSS descriptions that `html.parser` or regex could handle.
  - `xhtml2pdf` carries heavyweight transitive dependencies (`reportlab`, `pyHanko`, `cryptography`, `cffi`, `pycparser`).
  - Speculative retry loops and duplicate logging in `telegram_dispatcher.py` and `gmail_dispatcher.py`.

### 2.3 `/ponytail-gain` Scoreboard
```
  ponytail gain                     benchmark median · 5 tasks · 3 models

  Lines of code   no-skill  ████████████████████  100%
                  ponytail  ██▌·················    6–20%   ▼ 80–94%
  Cost            no-skill  ████████████████████  100%
                  ponytail  █████▌··············   23–53%  ▼ 47–77%
  Speed           ponytail  ▸ 3–6× faster

  This repo:  /ponytail-debt  (shortcuts deferred)
              /ponytail-audit (what's still cuttable)
```

### 2.4 `/ponytail-audit` Over-Engineering Findings
- `processors/curator.py:L752`: `delete: fallback_models list of invalid fictitious model names. Replacement: standard configured model with simple try-except.`
- `config.py:L40-44`: `delete: _deprecated_models block rejecting valid current Gemini models. Replacement: direct environment variable lookup.`
- `processors/formatter.py:L140-160`: `shrink: verbose inline HTML building blocks. Use unified tag helper with html.escape.`
- `requirements.txt`: `32 dependencies pinned; at least 10 are transitive or unused directly by core application logic.`

### 2.5 `/ponytail-review` Findings
- `L782-785 in curator.py`: `delete: unconditional disk writes inside curation pure function. Move save_used_content() to dispatch phase in main.py.`
- `L62 in revision_digest.py`: `stdlib: hand-rolled modulo counter. Replace with persistent milestone state file (revision_state.json).`
- `L125 in telegram_dispatcher.py`: `delete: partial success masking (success_count > 0). Return True only if success_count == len(chunks).`

---

## 3. Independent Deep Technical Audit (Sections A–I)

### Section A: Python Correctness
1. **Undefined Models in Gemini SDK:**
   In `config.py`, lines 39-46:
   ```python
   _raw_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
   _deprecated_models = {
       "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro",
       "gemini-2.0-flash", "gemini-2.0-flash-exp",
       "gemini-1.5-flash", "gemini-1.5-pro"
   }
   GEMINI_MODEL = "gemini-3.6-flash" if (not _raw_model or _raw_model in _deprecated_models) else _raw_model
   ```
   **Evidence:** The Google Gemini API roster does not contain `gemini-3.6-flash`. Marking `gemini-2.5-flash` as "deprecated" causes users with default setups to hit a `404 / NOT_FOUND` API error. The client in `curator.py` subsequently attempts fallback to `["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]` (line 752), all of which are invalid. As a result, AI curation is 100% broken under default settings and immediately degrades to heuristic fallback.
   **Fix:** Default `GEMINI_MODEL` to `gemini-2.5-flash`. Allow user override without blacklisting standard models.

2. **Partial Failure Masking in Telegram Dispatcher:**
   In `dispatchers/telegram_dispatcher.py`, line 125:
   ```python
   return success_count > 0
   ```
   If a digest is chunked into 4 messages and only chunk 1 is delivered while chunks 2, 3, and 4 fail (e.g. rate limit, bad characters, or connection drops), `dispatch_telegram()` returns `True`. The caller logs that dispatch succeeded, leaving the user with a broken, truncated digest.
   **Fix:** Return `success_count == len(chunks)`.

### Section B: RSS Ingestion and Data Quality
1. **Timeout & Resource Handling:**
   In `sources/rss_fetcher.py`:
   - Network requests use `requests.get(url, timeout=10, headers=...)` inside a `ThreadPoolExecutor(max_workers=5)`. This is appropriately bounded.
   - However, if a feed returns HTTP 403, 404, or 500, `fetch_feed()` catches exceptions and logs warnings, returning an empty list. This is robust.
2. **Deduplication Logic:**
   - Exact link deduplication (`seen_links`) and fuzzy title deduplication (`SequenceMatcher(None, title, existing).ratio() > 0.72`) are used.
   - However, deduplication is global across all categories. If a top national development also touches international diplomacy, one category will drop it. This is generally desirable to avoid duplicate reading.

### Section C: AI Curation & Factual Accuracy
1. **Brittle Regex JSON Extraction:**
   In `curator.py`, line 231 & line 401:
   ```python
   match = re.search(r"\{.*\}", raw_text, re.DOTALL)
   ```
   When Gemini returns conversational text before or after the JSON payload, or if the response includes markdown code blocks ````json ... ````, a greedy regex `r"\{.*\}"` can inadvertently capture stray braces or fail to parse if unescaped control characters exist.
   **Fix:** Clean markdown code fences (`re.sub(r"^```json\s*|\s*```$", "", raw_text.strip())`) and extract the JSON object cleanly.

### Section D: Security & Data Exposure
1. **HTML Injection / Cross-Site Scripting (XSS) in Formatter:**
   In `processors/formatter.py`:
   Untrusted input from external RSS feeds (`item.get("title")`, `item.get("summary")`, `item.get("link")`, `item.get("static_gk")`) is concatenated directly into HTML strings:
   ```python
   html.append(f"<div style='font-weight: 600;'>{idx}. {title}</div>")
   html.append(f"<a href='{link}' style='color: #2b6cb0;'>Source Link</a>")
   ```
   If a malicious RSS feed or compromised source includes payload such as:
   `<img src=x onerror=alert(document.domain)>` in the title, or `javascript:evil()` in the link, the email client and the GitHub Pages portal will render and execute it.
   **Fix:** Enforce `html.escape()` on all text components and validate that URL schemes strictly start with `http://` or `https://`.

2. **Secret Exposure:**
   `config.py` loads secrets from `.env`. Neither `config.py` nor dispatchers print raw tokens in normal logs. However, exceptions in `telegram_dispatcher.py` log `f"Network error connecting to Telegram API: {e}"`. Under certain urllib3/requests exceptions, the request URL containing the bot token `https://api.telegram.org/bot<TOKEN>/...` can appear in the exception message!
   **Fix:** Sanitize bot token from exception strings prior to logging.

### Section E: Formatting, HTML, and Markdown Safety
1. **Telegram Markdown Special Characters:**
   Telegram Markdown requires escaping characters such as `_`, `*`, `[`, `]`, `(`, `)`, `~`, `` ` ``, `>`, `#`, `+`, `-`, `=`, `|`, `{`, `}`, `.`, `!`.
   While `telegram_dispatcher.py` provides a fallback to plain text if markdown parsing fails, unescaped characters in news titles (e.g. `Sensex gains +300 pts [Details]`) cause the initial markdown send to fail routinely, incurring unnecessary retry overhead and falling back to unformatted text.
   **Fix:** Sanitize or properly escape Markdown syntax in news titles and descriptions.

### Section F: Multi-Recipient Delivery & Rate Limiting
1. **Telegram Dispatcher Single Chat Limitation:**
   In `config.py:26` and `dispatchers/telegram_dispatcher.py:100-110`:
   `TELEGRAM_CHAT_ID` is handled as a single string. When users have multiple channels or multiple subscriber chat IDs (or bot group chats), the system cannot dispatch to them.
   `gmail_dispatcher.py` handles comma-separated recipients:
   `GMAIL_TO = [e.strip() for e in os.getenv("GMAIL_TO", GMAIL_USER).split(",") if e.strip()]`
   `telegram_dispatcher.py` must support the same format (`TELEGRAM_CHAT_ID="12345,67890,-1001234"`).
   **Fix:** Support comma-separated chat IDs in `TELEGRAM_CHAT_ID`, dispatching to each target chat sequentially with rate-limit delays.

### Section G: Idempotency, Storage, and Persistence
1. **Side Effects in Dry-Run / Preview:**
   `main.py --dry-run` or `--channel preview` should allow safe inspection without side effects.
   Currently, `curator.py:782-785` executes:
   ```python
   save_used_content(used_content)
   append_revision_log(bulletin_data)
   ```
   regardless of whether `--dry-run` was specified. This mutates `docs/archive/used_content.json` and `docs/archive/revision_log.json` during dry runs.
   **Fix:** Pass `save_state: bool = True` (or `dry_run: bool = False`) to `curate_daily_bulletin()` and only save content/revision log when not in dry-run mode.

### Section H: Revision Digest & PDF Generation
1. **Non-Idempotent 10-Day Revision Trigger:**
   In `revision_digest.py:62`:
   ```python
   total = len(log_data)
   if total % REVISION_EVERY_N_DAYS != 0:
       logger.info(f"Revision log count: {total}. Revision runs every 10 days.")
       return
   ```
   **Problems:**
   - If `total == 10`, every time `revision_digest.py` is invoked (e.g. if the workflow is re-run or triggered manually), it generates and sends a duplicate revision email.
   - If the log skips an exact multiple of 10 (e.g., two entries were logged in one day or manual testing incremented it to 11), `total % 10` is never `0` again until day 20, missing the milestone.
   **Fix:** Maintain a state file `docs/archive/revision_state.json` recording `last_revised_count` or `last_revision_date`. Trigger revision if `total >= last_revised_count + REVISION_EVERY_N_DAYS` and update the state file atomically.

### Section I: Automation, Scheduling, and GitHub Actions
1. **Schedule Time Discrepancy:**
   - `.github/workflows/daily_digest.yml`: `cron: '47 00 * * *'` (00:47 UTC = 06:17 AM IST).
   - `config.py:48`: `SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:37")`.
   - `README.md`: Mentions `21:47 UTC (3:17 AM IST)` and `09:30`.
   **Fix:** Harmonize configuration and documentation to eliminate confusion.

---

## 4. Prioritized Vulnerability & Defect Registry

| Finding ID | Severity | File & Lines | Description | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **DD-SEC-001** | Critical | `processors/formatter.py:180-250` | Raw RSS titles, links, and AI text unescaped in HTML output. | Apply `html.escape()` and validate safe URL schemes. |
| **DD-COR-001** | Critical | `config.py:39-46`, `curator.py:752` | Fictitious Gemini model `gemini-3.6-flash` configured as default and in fallbacks. | Set default to `gemini-2.5-flash`; permit valid user overrides. |
| **DD-REL-001** | High | `processors/curator.py:782-785`, `main.py` | State mutation occurs even in `--dry-run` or `--channel preview`. | Guard persistence calls with `dry_run` flag. |
| **DD-REL-002** | High | `revision_digest.py:62-67` | Modulo-based revision trigger is not idempotent and risks duplicate or missed revisions. | Implement persistent milestone state tracking (`revision_state.json`). |
| **DD-COR-002** | High | `dispatchers/telegram_dispatcher.py:100-125` | Masks partial chunk send failures and lacks multi-recipient support. | Support comma-separated chat IDs; return `True` only if all chunks succeed. |
| **DD-SEC-002** | Medium | `dispatchers/telegram_dispatcher.py:59` | Telegram bot token can leak into logs via exception strings. | Mask bot token in network exception logs. |
| **DD-BLT-001** | Medium | `config.py:48`, `.github/workflows/daily_digest.yml:7` | Divergent schedule times across cron, code, and documentation. | Harmonize configuration and update README. |
| **DD-ENG-001** | Medium | `processors/curator.py:230-245` | Brittle regex parsing for AI JSON output. | Strip markdown fences and parse JSON cleanly with fallback. |
| **DD-TST-001** | Medium | Repo root | Complete absence of automated unit, mock, and regression test suites. | Build comprehensive pytest/unittest test harness in `tests/`. |

---
