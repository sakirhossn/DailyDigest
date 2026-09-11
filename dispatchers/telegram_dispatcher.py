"""
Telegram Dispatcher for Daily Current Affairs Agent.
Sends curated current affairs chunks to a Telegram chat or channel via Bot API.
"""

import logging
import sys
import time
from pathlib import Path
from typing import List, Optional
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


def test_telegram_connection(bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Verifies that the bot token is valid and can access the given chat."""
    token = (bot_token or TELEGRAM_BOT_TOKEN).strip()
    target_chat = (chat_id or TELEGRAM_CHAT_ID).strip()

    if not token or not target_chat:
        logger.error("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")
        return False

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if not data.get("ok"):
            logger.error(f"Telegram getMe failed: {data.get('description')}")
            return False

        bot_username = data.get("result", {}).get("username")
        logger.info(f"Connected to Telegram Bot: @{bot_username}")

        # Send quick verification ping
        test_msg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        ping_res = requests.post(
            test_msg_url,
            json={
                "chat_id": target_chat,
                "text": "🤖 *Daily Current Affairs Agent* connected successfully!",
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
        ping_data = ping_res.json()
        if ping_data.get("ok"):
            logger.info(f"Test message sent successfully to chat_id: {target_chat}")
            return True
        else:
            logger.error(f"Failed to send test message: {ping_data.get('description')}")
            return False

    except Exception as e:
        logger.error(f"Network error connecting to Telegram API: {e}")
        return False


def send_single_chunk(token: str, chat_id: str, text: str, retries: int = 2) -> bool:
    """Sends a single message chunk to Telegram with fallback to plain text if markdown errors."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for attempt in range(retries + 1):
        try:
            # First try with Markdown
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            res = requests.post(url, json=payload, timeout=15)
            data = res.json()

            if data.get("ok"):
                return True

            # If Markdown parsing failed, try sending as plain text
            logger.warning(f"Markdown send failed ({data.get('description')}). Retrying as plain text...")
            payload.pop("parse_mode", None)
            res_plain = requests.post(url, json=payload, timeout=15)
            data_plain = res_plain.json()
            if data_plain.get("ok"):
                return True

            logger.error(f"Telegram sendMessage error: {data_plain.get('description')}")

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")

        time.sleep(1)

    return False


def dispatch_telegram(chunks: List[str], bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Dispatches all formatted message chunks to Telegram."""
    token = (bot_token or TELEGRAM_BOT_TOKEN).strip()
    target_chat = (chat_id or TELEGRAM_CHAT_ID).strip()

    if not token or not target_chat:
        logger.error("Cannot dispatch to Telegram: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured in .env")
        return False

    logger.info(f"Dispatching {len(chunks)} message chunks to Telegram chat {target_chat}...")
    success_count = 0

    for i, chunk in enumerate(chunks, 1):
        if send_single_chunk(token, target_chat, chunk):
            success_count += 1
            # Brief delay to respect Telegram rate limits
            time.sleep(0.5)
        else:
            logger.error(f"Failed to deliver chunk {i}/{len(chunks)}.")

    if success_count == len(chunks):
        logger.info("All Telegram message chunks delivered successfully!")
        return True
    else:
        logger.warning(f"Delivered {success_count}/{len(chunks)} chunks to Telegram.")
        return success_count > 0


if __name__ == "__main__":
    print("Testing Telegram connection with configured credentials...")
    test_telegram_connection()
