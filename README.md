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
- ❓ **Daily 5 Exam MCQs:** Generates exam-standard practice questions with options, correct answer, and detailed explanations.
- 📱 **Telegram Delivery:** Clean Markdown messages with emojis, source hyperlinks, spoiler-tagged quiz answers, and automatic chunking under Telegram's 4096-character limit.
- ✉️ **Gmail Delivery:** Modern, responsive HTML email template featuring light/dark support, topic badges, and expandable answer keys.
- 🤖 **AI-Powered & Resilient:** Uses Google Gemini (`gemini-2.5-flash`) for deep synthesis when configured, and features a built-in heuristic rule engine that works 100% offline without any API keys.
- ⏰ **Multiple Automation Options:** Run via built-in scheduler, Windows Task Scheduler, or free 24/7 cloud automation using GitHub Actions.

---

## 🚀 Quick Start (Preview in 5 Seconds)

The agent works immediately out of the box with zero setup for previewing!

```powershell
# Navigate to project folder
cd ".gemini\antigravity\scratch\exam-current-affairs-agent"

# Run dry-run preview in console and save HTML digest locally
.\.venv\Scripts\python.exe main.py --exam all --channel preview --save-html daily_digest.html
```

You can open `daily_digest.html` in any browser to inspect the Gmail newsletter template.

---

## ⚙️ Configuration (.env)

Edit the `.env` file in the project folder to set up your credentials:

```ini
# Exam Focus: UPSC | BANK | SSC | RRB | ALL
TARGET_EXAM=ALL

# Delivery Channel: telegram | gmail | both | preview
DISPATCH_CHANNEL=both

# Daily Morning Schedule Time (24-hour format)
SCHEDULE_TIME=09:17

# Telegram Bot (Optional, needed for Telegram)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id

# Gmail SMTP (Optional, needed for Gmail)
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
GMAIL_TO=your_email@gmail.com

# Gemini AI (Optional, for deep exam synthesis)
GEMINI_API_KEY=your_gemini_api_key
```

---

## 🔑 Credential Setup Guides

### 1. Telegram Bot (Takes 1 Minute)
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, give it a name and a username (e.g. `MyExamDailyBot`).
3. Copy the **HTTP API token** and set `TELEGRAM_BOT_TOKEN`.
4. Open [@userinfobot](https://t.me/userinfobot) and send `/start` to view your numeric **Chat ID**, then set `TELEGRAM_CHAT_ID`.
5. Start your new bot by opening its chat and clicking **Start**.

### 2. Gmail App Password (Takes 1 Minute)
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is enabled.
3. Search for **App passwords** (or visit [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Enter an app name (e.g. `Exam Agent`) and click **Create**.
5. Copy the 16-letter code and set `GMAIL_APP_PASSWORD`.

### 3. Google Gemini API (Free)
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey).
2. Click **Create API key** and paste it into `GEMINI_API_KEY`.
*(Note: If omitted, the agent will gracefully run its heuristic classifier).*

---

## 🛠️ CLI Usage & Flags

```powershell
# 1. Test your Telegram or Gmail credentials
.\.venv\Scripts\python.exe main.py --test-connection --channel both

# 2. Run specifically for UPSC and send to Telegram
.\.venv\Scripts\python.exe main.py --exam upsc --channel telegram

# 3. Run specifically for Banking exams and send to Gmail
.\.venv\Scripts\python.exe main.py --exam bank --channel gmail

# 4. Run for SSC / RRB and send to both
.\.venv\Scripts\python.exe main.py --exam ssc --channel both

# 5. Keep running the background scheduler (runs daily at 09:17 AM)
.\.venv\Scripts\python.exe main.py --daemon
```

---

## ⏰ Automated Scheduling

### Option 1: Free GitHub Actions (Recommended — Runs in Cloud)
1. Push this repository to a private GitHub repository.
2. Go to **Settings > Secrets and variables > Actions > Repository secrets**.
3. Add the secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `GEMINI_API_KEY`.
4. The workflow in `.github/workflows/daily_digest.yml` will automatically execute every morning at 09:17 AM IST.

### Option 2: Windows Task Scheduler (Runs on your PC)
Run this command in PowerShell to create a daily 09:17 AM scheduled task on Windows:

```powershell
$action = New-ScheduledTaskAction -Execute ".gemini\antigravity\scratch\exam-current-affairs-agent\.venv\Scripts\python.exe" -Argument "main.py --channel both" -WorkingDirectory ".gemini\antigravity\scratch\exam-current-affairs-agent"
$trigger = New-ScheduledTaskTrigger -Daily -At "09:17AM"
Register-ScheduledTask -TaskName "DailyExamCurrentAffairs" -Action $action -Trigger $trigger -Description "Dispatches Daily Current Affairs to Telegram and Gmail"
```
