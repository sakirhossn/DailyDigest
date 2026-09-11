"""
Main entry point for Daily Current Affairs Agent.
Provides CLI interface for fetching news, curating exam-tailored digests,
and dispatching via Telegram and/or Gmail.
"""

import argparse
import datetime
import logging
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Ensure Windows console supports Unicode (e.g. ₹ rupee symbol, quotes)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    DISPATCH_CHANNEL,
    GEMINI_API_KEY,
    GMAIL_TO,
    TARGET_EXAM,
    VALID_CHANNELS,
    VALID_EXAMS,
)
from dispatchers.gmail_dispatcher import dispatch_gmail, test_gmail_connection
from dispatchers.telegram_dispatcher import dispatch_telegram, test_telegram_connection
from processors.curator import curate_daily_bulletin
from processors.formatter import (
    format_gmail_html,
    format_plain_text,
    format_telegram_chunks,
)
from sources.rss_fetcher import fetch_all_current_affairs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_agent(
    exam_type: str = TARGET_EXAM,
    channel: str = DISPATCH_CHANNEL,
    dry_run: bool = False,
    save_html_path: str = None,
) -> bool:
    """Executes the full pipeline: Fetch -> Curate -> Format -> Dispatch."""
    logger.info(f"--- Starting Current Affairs Agent Pipeline ---")
    logger.info(f"Target Exam: {exam_type} | Channel: {channel} | Dry Run: {dry_run}")

    # 1. Fetch live articles
    logger.info("Step 1: Fetching current affairs from RSS feeds...")
    raw_articles = fetch_all_current_affairs()
    if not raw_articles:
        logger.error("No articles could be retrieved. Aborting dispatch.")
        return False

    # 2. Curate and structure for exam
    logger.info(f"Step 2: Curating exam-focused bulletin for {exam_type}...")
    bulletin = curate_daily_bulletin(raw_articles, exam_type=exam_type, api_key=GEMINI_API_KEY)

    # 3. Format digests
    logger.info("Step 3: Formatting digests...")
    telegram_chunks = format_telegram_chunks(bulletin)
    gmail_html = format_gmail_html(bulletin)
    plain_text = format_plain_text(bulletin)

    # Optional local save
    if save_html_path:
        out_file = Path(save_html_path)
        out_file.write_text(gmail_html, encoding="utf-8")
        logger.info(f"Saved HTML digest to: {out_file.resolve()}")

    # If dry run or preview, print to console and exit
    if dry_run or channel == "preview":
        print("\n" + "=" * 70)
        print(f"PREVIEW: DAILY CURRENT AFFAIRS DIGEST ({exam_type})")
        print("=" * 70)
        print(plain_text)
        print("\n" + "=" * 70)
        print(f"Telegram chunk count: {len(telegram_chunks)}")
        print(f"Gmail HTML character length: {len(gmail_html)}")
        print("=" * 70)
        return True

    # 4. Dispatch via chosen channel
    subject = f"🎯 Daily Current Affairs ({exam_type}) - {bulletin.get('date')}"
    from config import GMAIL_APP_PASSWORD, GMAIL_USER, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

    has_telegram = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
    has_gmail = bool(GMAIL_USER and GMAIL_APP_PASSWORD)

    dispatched_any = False

    if channel in ["telegram", "both"]:
        if has_telegram:
            logger.info("Step 4a: Dispatching to Telegram...")
            tg_ok = dispatch_telegram(telegram_chunks)
            if tg_ok:
                dispatched_any = True
        else:
            if channel == "telegram":
                logger.error("Telegram credentials missing in .env. Cannot dispatch to Telegram.")
            else:
                logger.info("ℹ️ Telegram credentials not configured. Skipping Telegram.")

    if channel in ["gmail", "both"]:
        if has_gmail:
            logger.info("Step 4b: Dispatching to Gmail...")
            gm_ok = dispatch_gmail(gmail_html, plain_text, subject=subject)
            if gm_ok:
                dispatched_any = True
        else:
            if channel == "gmail":
                logger.error("Gmail credentials missing in .env. Cannot dispatch to Gmail.")
            else:
                logger.info("ℹ️ Gmail credentials not configured. Skipping Gmail.")

    if not dispatched_any and channel != "preview":
        logger.warning(
            "⚠️ No messages were dispatched because credentials for your chosen channel(s) are not configured. "
            "Please update .env (or GitHub Secrets) with your credentials."
        )

    logger.info("--- Pipeline Completed ---")
    return dispatched_any


def main():
    parser = argparse.ArgumentParser(
        description="Daily Current Affairs Agent for SSC, RRB, Bank, and UPSC exams."
    )
    parser.add_argument(
        "--exam",
        choices=[e.lower() for e in VALID_EXAMS],
        default=TARGET_EXAM.lower(),
        help="Target exam syllabus (upsc, bank, ssc, rrb, all)",
    )
    parser.add_argument(
        "--channel",
        choices=VALID_CHANNELS,
        default=DISPATCH_CHANNEL,
        help="Delivery channel (telegram, gmail, both, preview)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and curate without sending messages (prints preview to console)",
    )
    parser.add_argument(
        "--save-html",
        metavar="PATH",
        default=None,
        help="Path to save the generated HTML digest locally (e.g. daily_digest.html)",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test Telegram bot and/or Gmail credentials and exit",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Start the background scheduler to run every morning",
    )

    args = parser.parse_args()

    if args.test_connection:
        print("--- Testing Credentials ---")
        if args.channel in ["telegram", "both"]:
            print("\n[Telegram Test]")
            test_telegram_connection()
        if args.channel in ["gmail", "both"]:
            print("\n[Gmail Test]")
            test_gmail_connection()
        return

    if args.daemon:
        from scheduler import start_scheduler
        start_scheduler(exam_type=args.exam.upper(), channel=args.channel)
        return

    # Normal one-shot execution
    run_agent(
        exam_type=args.exam.upper(),
        channel=args.channel,
        dry_run=args.dry_run,
        save_html_path=args.save_html,
    )


if __name__ == "__main__":
    main()
