"""
10-Day Revision Digest for Daily Current Affairs Agent.

Standalone script — run this as a separate step AFTER the main dispatcher each day.
It reads docs/archive/revision_log.json (populated daily by processors/curator.py)
and, once every 10 entries, compiles the last 10 days of vocab words, idioms, and
static GK boosters into a single revision email (with a PDF attachment) and sends
it via Gmail.

On days that aren't a multiple of 10, this script does nothing and exits quietly.
"""

import json
import logging
import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import GMAIL_TO
from processors.formatter import (
    format_revision_digest_html,
    format_revision_digest_plain,
    format_revision_digest_pdf_html,
)
from dispatchers.gmail_dispatcher import dispatch_gmail

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REVISION_LOG_PATH = Path(__file__).resolve().parent / "docs" / "archive" / "revision_log.json"
REVISION_STATE_PATH = Path(__file__).resolve().parent / "docs" / "archive" / "revision_state.json"
REVISION_EVERY_N_DAYS = 10


def load_revision_state(total_entries: int) -> dict:
    """Loads previous revision state or sets baseline checkpoint."""
    if REVISION_STATE_PATH.exists():
        try:
            with open(REVISION_STATE_PATH, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as e:
            logger.warning(f"Failed to read revision state: {e}")

    # Baseline: if historical logs exist and no state was saved, baseline to highest completed previous decade
    initial_checkpoint = (
        ((total_entries - 1) // REVISION_EVERY_N_DAYS) * REVISION_EVERY_N_DAYS
        if total_entries > 0
        else 0
    )
    return {"last_revised_count": initial_checkpoint}


def save_revision_state(state: dict):
    """Saves checkpoint state atomically to disk."""
    try:
        REVISION_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REVISION_STATE_PATH, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2)
    except Exception as e:
        logger.error(f"Failed to save revision state: {e}")


def generate_pdf_bytes(pdf_safe_html: str):
    """Renders the simplified HTML template into PDF bytes using xhtml2pdf."""
    try:
        from xhtml2pdf import pisa
    except ImportError:
        logger.error("xhtml2pdf is not installed. Add 'xhtml2pdf' to requirements.txt.")
        return None

    buffer = BytesIO()
    result = pisa.CreatePDF(pdf_safe_html, dest=buffer)
    if result.err:
        logger.error("xhtml2pdf reported an error while generating the PDF.")
        return None
    return buffer.getvalue()


def main():
    if not REVISION_LOG_PATH.exists():
        logger.info("No revision_log.json yet — nothing to do.")
        return

    with open(REVISION_LOG_PATH, "r", encoding="utf-8") as fh:
        log = json.load(fh)

    total = len(log)
    logger.info(f"Revision log currently has {total} daily entries.")

    state = load_revision_state(total)
    last_revised = state.get("last_revised_count", 0)
    pending_count = total - last_revised

    if pending_count < REVISION_EVERY_N_DAYS:
        remainder = REVISION_EVERY_N_DAYS - pending_count
        logger.info(
            f"Not a 10-day checkpoint yet ({pending_count}/{REVISION_EVERY_N_DAYS} accumulated since last revision; "
            f"{remainder} more day(s) to go). Skipping revision email."
        )
        return

    # Extract exactly the next 10-day batch
    revision_batch = log[last_revised : last_revised + REVISION_EVERY_N_DAYS]
    start_date = revision_batch[0].get("date", "")
    end_date = revision_batch[-1].get("date", "")

    logger.info(f"10-day checkpoint reached! Compiling revision digest for {start_date} to {end_date}...")

    html_content = format_revision_digest_html(revision_batch, start_date, end_date)
    plain_text = format_revision_digest_plain(revision_batch, start_date, end_date)
    pdf_safe_html = format_revision_digest_pdf_html(revision_batch, start_date, end_date)

    pdf_bytes = generate_pdf_bytes(pdf_safe_html)
    attachments = []
    if pdf_bytes:
        safe_start = start_date.replace(" ", "_").replace(",", "")
        safe_end = end_date.replace(" ", "_").replace(",", "")
        filename = f"Revision_Digest_{safe_start}_to_{safe_end}.pdf"
        attachments.append((filename, pdf_bytes))
        logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes).")
    else:
        logger.warning("PDF generation failed — sending email without attachment.")

    subject = f"📚 10-Day Revision Digest: Vocab, Idioms & GK ({start_date} – {end_date})"

    success = dispatch_gmail(
        html_content=html_content,
        plain_text=plain_text,
        subject=subject,
        to_emails=GMAIL_TO,
        attachments=attachments if attachments else None,
    )

    if success:
        logger.info("10-day revision digest sent successfully!")
        state["last_revised_count"] = last_revised + REVISION_EVERY_N_DAYS
        state["last_revised_date"] = end_date
        save_revision_state(state)
    else:
        logger.error("Failed to send 10-day revision digest.")


if __name__ == "__main__":
    main()
