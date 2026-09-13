# 🎯 Exam Current Affairs Agent

An automated, intelligent current affairs curation and delivery agent designed for competitive exam aspirants (**UPSC, Banking [IBPS/SBI/RBI], SSC, and RRB**).

The agent collects real-time news from verified sources (Press Information Bureau, The Hindu, Livemint, Economic Times, DD News), filters and categorizes them according to specific exam syllabus patterns, generates **5 daily practice MCQs with explanations**, and dispatches the briefing to **Telegram** and/or **Gmail**.

---

## ✨ Features

- 📰 **Multi-Source Ingestion:** Concurrently ingests and deduplicates articles from PIB, national newspapers, and financial wires.
- 🎯 **Exam-Tailored Curation:**
  - **UPSC:** GS-1 to GS-4 paper categorization, constitutional articles, government policies, Prelims facts, and Mains analytical angles.
  - **Banking (IBPS, SBI, RBI Grade B):** Heavy focus on RBI notifications, monetary policy, GDP forecasts, banking mergers, MoUs, and financial awareness terms.
  - **SSC & RRB:** Crisp one-liner facts, appointments, awards, military exercises, sports championships, and static GK links.
  - **ALL:** Comprehensive multi-section digest covering all exam aspects.
- ❓ **Daily 5 Exam MCQs:** Generates exam-standard practice questions with options, correct answer, and detailed explanations based on the day's news.
- 📱 **Telegram Delivery:** Clean Markdown messages with emojis, source hyperlinks, spoiler-tagged quiz answers, and automatic chunking under Telegram's 4096-character limit.
- ✉️ **Gmail Delivery:** Modern, responsive HTML email template featuring light/dark mode support, topic badges, and expandable answer keys.
- 🤖 **AI-Powered & Resilient:** Uses Google Gemini (`gemini-3.6-flash`) for deep synthesis when configured, and features a built-in heuristic rule engine that works 100% offline without any API keys.
- ⏰ **Multiple Automation Options:** Run via a built-in scheduler, Windows Task Scheduler/cron, or free 24/7 cloud automation using GitHub Actions.
- 📚 **Automated Revision:** Generates and emails a 10-day revision digest with a PDF attachment, compiling all vocab, idioms, and static GK points.
- 🌐 **Web Archive:** Automatically archives every daily digest to a browsable web interface with a calendar-based navigator, powered by GitHub Pages.

---

## 🚀 Quick Start (Preview in 5 Seconds)

The agent works immediately out of the box with zero setup for previewing. First, set up the project:

```powershell
# Clone the repository
git clone https://github.com/sakirhossn/DailyDigest.git
cd DailyDigest

# Create a virtual environment and activate it
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

Now, run a dry-run to preview the output in your console and save a local HTML copy:

```powershell
# Run a dry-run preview and save the HTML digest
python main.py --exam all --channel preview --save-html daily_digest.html
```

You can open `daily_digest.html` in any browser to inspect the full Gmail newsletter template.

---

## ⚙️ Configuration

Create a file named `.env` in the project's root directory and populate it with your settings. You can use the following template:

```ini
# Exam Focus: UPSC | BANK | SSC | RRB | ALL
TARGET_EXAM=ALL

# Delivery Channel: telegram | gmail | both | preview
DISPATCH_CHANNEL=both

# Daily Schedule Time (24-hour format, used by local --daemon scheduler)
# e.g., 09:30 for 9:30 AM system time
SCHEDULE_TIME=09:30

# --- Credentials (only fill what you need) ---

# Telegram Bot (Optional, for Telegram delivery)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_personal_or_channel_chat_id

# Gmail SMTP (Optional, for Gmail delivery)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_TO=your_email@gmail.com,another_email@example.com

# Google Gemini AI (Optional, for AI-powered curation)
# If omitted, the agent uses its built-in heuristic engine.
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🔑 Credential Setup Guides

### 1. Telegram Bot (1 Minute)
1. Open Telegram and search for **[@BotFather](https://t.me/BotFather)**.
2. Send `/newbot`, give it a name (e.g., `My Exam Digest`) and a username (e.g., `MyExamDigestBot`).
3. Copy the **HTTP API token** and set `TELEGRAM_BOT_TOKEN` in your `.env` file.
4. To get your chat ID, search for **[@userinfobot](https://t.me/userinfobot)**, send `/start`, and copy the numeric **Chat ID**. Set this as `TELEGRAM_CHAT_ID`.
5. Start your new bot by opening its chat and clicking **Start**.

### 2. Gmail App Password (1 Minute)
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is enabled.
3. Search for **App passwords** (or visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Under "Select app", choose "Mail". Under "Select device", choose "Windows Computer". Click **Generate**.
5. Copy the 16-letter code (without spaces) and set `GMAIL_APP_PASSWORD` in your `.env` file.

### 3. Google Gemini API Key (Free)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API key** and copy it into the `GEMINI_API_KEY` field in your `.env` file.
*(Note: The agent will run perfectly without this key, using its offline heuristic engine.)*

---

## 🛠️ CLI Usage

You can run the agent manually with different configurations using command-line flags.

```powershell
# 1. Test your Telegram and/or Gmail credentials
python main.py --test-connection --channel both

# 2. Run for UPSC and send only to Telegram
python main.py --exam upsc --channel telegram

# 3. Run for Banking exams and send only to Gmail
python main.py --exam bank --channel gmail

# 4. Run for SSC/RRB and send to both channels
python main.py --exam ssc --channel both

# 5. Start the background scheduler (runs daily at the time set in SCHEDULE_TIME)
python main.py --daemon
```

---

## ⏰ Automated Scheduling

### Option 1: Free GitHub Actions (Recommended — Runs 24/7 in the Cloud)
1. Fork this repository to your own GitHub account.
2. Go to your forked repository's **Settings > Secrets and variables > Actions**.
3. Under **Repository secrets**, add the secrets you configured in your `.env` file: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GMAIL_TO`, and `GEMINI_API_KEY`.
4. The workflow in `.github/workflows/daily_digest.yml` will automatically run every morning at **21:47 UTC** (3:17 AM IST), dispatch the digest, archive it, and check if a revision email needs to be sent.

### Option 2: Windows Task Scheduler (Runs on your PC)
Run this command in PowerShell (from the project's root directory) to create a daily scheduled task.

```powershell
# This command assumes your project is in the current directory.
# It will create a task to run daily at 9:30 AM.
$projectPath = (Get-Location).Path
$pythonPath = Join-Path $projectPath ".venv\Scripts\python.exe"
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "main.py --channel both" -WorkingDirectory $projectPath
$trigger = New-ScheduledTaskTrigger -Daily -At "9:30AM"
Register-ScheduledTask -TaskName "DailyExamCurrentAffairs" -Action $action -Trigger $trigger -Description "Dispatches Daily Current Affairs to Telegram and Gmail."
