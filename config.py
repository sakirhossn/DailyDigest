"""
Configuration settings for the Daily Current Affairs Agent.
Loads configuration from environment variables (.env file supported).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Target Exam Options
VALID_EXAMS = ["UPSC", "BANK", "SSC", "RRB", "ALL"]
_raw_exam = os.getenv("TARGET_EXAM", "ALL").strip().upper()
TARGET_EXAM = _raw_exam if _raw_exam in VALID_EXAMS else "ALL"

# Delivery Channel Options: telegram, gmail, both, preview
VALID_CHANNELS = ["telegram", "gmail", "both", "preview"]
_raw_channel = os.getenv("DISPATCH_CHANNEL", "both").strip().lower()
DISPATCH_CHANNEL = _raw_channel if _raw_channel in VALID_CHANNELS else "both"

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Gmail SMTP Settings
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()
GMAIL_TO = [
    email.strip()
    for email in os.getenv("GMAIL_TO", GMAIL_USER).split(",")
    if email.strip()
]

# AI Intelligence (Gemini API)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Fallback AI Providers (Optional keys for resilience)
# OpenRouter (FREE — access to Llama 3.3, Qwen 2.5, Mistral: https://openrouter.ai/keys)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()

# Groq (FREE tier — high speed: https://console.groq.com/)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# OpenAI (paid — gpt-4o-mini: https://platform.openai.com/api-keys)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

# Scheduling
SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "09:37").strip()

# Verified RSS Feeds for Exam Topics
RSS_FEEDS = {
    "National & Governance": [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://ddnews.gov.in/en/category/national/feed/",
        "https://news.google.com/rss/search?q=Cabinet+decision+OR+PIB+OR+%22government+scheme%22+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Economy & Banking": [
        "https://www.thehindu.com/business/Economy/feeder/default.rss",
        "https://www.livemint.com/rss/economy",
        "https://news.google.com/rss/search?q=%22Reserve+Bank+of+India%22+OR+RBI+OR+SEBI+OR+inflation+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Defence, Science & Tech": [
        "https://www.thehindu.com/sci-tech/technology/feeder/default.rss",
        "https://news.google.com/rss/search?q=ISRO+OR+DRDO+OR+%22missile%22+OR+%22military+exercise%22+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "International & Bilateral": [
        "https://www.thehindu.com/news/international/feeder/default.rss",
        "https://news.google.com/rss/search?q=India+bilateral+summit+OR+G20+OR+BRICS+OR+UN+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
    "Sports, Awards & Appointments": [
        "https://news.google.com/rss/search?q=India+championship+OR+appointed+OR+honoured+award+when:1d&hl=en-IN&gl=IN&ceid=IN:en",
    ],
}
