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
REVISION_EVERY_N_DAYS = 10


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

    if total == 0 or total % REVISION_EVERY_N_DAYS != 0:
        remainder = REVISION_EVERY_N_DAYS - (total % REVISION_EVERY_N_DAYS)
        logger.info(f"Not a 10-day checkpoint yet ({remainder} more day(s) to go). Skipping revision email.")
        return

    last_10 = log[-REVISION_EVERY_N_DAYS:]
    start_date = last_10[0].get("date", "")
    end_date = last_10[-1].get("date", "")

    logger.info(f"10-day checkpoint reached! Compiling revision digest for {start_date} to {end_date}...")

    html_content = format_revision_digest_html(last_10, start_date, end_date)
    plain_text = format_revision_digest_plain(last_10, start_date, end_date)
    pdf_safe_html = format_revision_digest_pdf_html(last_10, start_date, end_date)

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
    else:
        logger.error("Failed to send 10-day revision digest.")


if __name__ == "__main__":
    main()
