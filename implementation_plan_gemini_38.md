# Implementation Plan: Gemini 3.8 Flash Upgrade & Model Roster Modernization

**Target Repository:** `https://github.com/sakirhossn/DailyDigest`  
**Date:** 2026-10-18  
**Objective:** Upgrade Google Gemini API model integration to the modern stable generation (`gemini-3.8-flash` & `gemini-3.5-flash-lite`), eliminating `404 NOT_FOUND` errors for new API keys and deprecating legacy 2.5/2.0/1.5 models.

---

## 1. Problem Diagnosis & Evidence

### Error Trace Observed from Live Run:
```
HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent "HTTP/1.1 404 Not Found"
[ERROR] Gemini (gemini-2.5-flash) curation failed: ClientError: 404 NOT_FOUND. {
  'error': {
    'code': 404,
    'message': 'This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.8-flash for the latest features and improvements.',
    'status': 'NOT_FOUND'
  }
}
[ERROR] Gemini (gemini-2.5-flash-lite) curation failed: ClientError: 404 NOT_FOUND. {
  'error': {
    'code': 404,
    'message': 'This model models/gemini-2.5-flash-lite is no longer available to new users. Please update your code to use models/gemini-3.5-flash-lite for the latest features and improvements.'
  }
}
```

### Root Cause:
The Gemini API in 2026 has sunset `gemini-2.5-flash` and `gemini-2.5-flash-lite` for newly provisioned user API keys. Google's API now strictly routes current generation traffic to:
- **`gemini-3.8-flash`** (Latest high-throughput general reasoning & synthesis model, released September 2026)
- **`gemini-3.5-flash-lite`** (Low-latency, lightweight fallback model, released July 2026)
- **`gemini-3.5-flash`** (High-efficiency multimodal model)

Legacy models (`gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*`) return 404 ClientError on new keys and force the system into offline heuristic fallback.

---

## 2. Proposed Changes

### Workstream 1: Configuration (`config.py`)
- Set default `GEMINI_MODEL = "gemini-3.8-flash"`.
- Reinstate `_deprecated_models` set to intercept legacy configurations (`gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-1.5-flash`) and automatically upgrade them to `gemini-3.8-flash`.

### Workstream 2: AI Curation Engine (`processors/curator.py`)
- Update candidate fallback sequence:
  `candidate_models = [GEMINI_MODEL, "gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]`
- Filter out deprecated models dynamically so that failed attempts do not waste retries on 404 endpoints.

### Workstream 3: Test Suite Updates (`tests/test_config.py`)
- Update `test_default_gemini_model_is_valid` to assert `gemini-3.8-flash`.
- Add test case verifying automatic migration from legacy model names to `gemini-3.8-flash`.

### Workstream 4: Documentation & Defaults (`README.md`, `.env.example`)
- Update model reference in `README.md` to `gemini-3.8-flash`.
- Ensure `.env.example` mentions `gemini-3.8-flash`.

---

## 3. Review Command Integration

1. **/gsd-code-review:** Verify model name correctness, retry chain soundness, and backward compatibility.
2. **/ponytail:** Enforce simplest implementation without extra dependencies or complex abstraction layers.
3. **/ponytail-gain:** Measure code footprint and efficiency impact.
4. **/ponytail-audit:** Scan for residual references to dead models or speculative fallbacks.
5. **/ponytail-review:** Line-by-line diff review before final commit.

---

## 4. Verification & Testing Strategy
- Execute `.\.venv\Scripts\python.exe -m unittest discover tests -v` to ensure 100% test pass rate.
- Run dry-run CLI verification: `.\.venv\Scripts\python.exe main.py --channel preview --dry-run`.
- Verify Git status and commit cleanly to a remediation branch, merge, and push to origin.
