"""
Formatter for Daily Current Affairs Agent.
Transforms structured bulletin data into Telegram-compatible messages (with chunking)
and styled, responsive HTML emails for Gmail.
"""

from typing import Dict, List


def format_telegram_chunks(bulletin: Dict) -> List[str]:
    """
    Formats the bulletin into a list of messages each under Telegram's 4096 char limit.
    Uses clean Markdown formatting with emojis and spoiler tags for quiz answers.
    """
    date = bulletin.get("date", "")
    exam = bulletin.get("exam_type", "ALL")
    headline = bulletin.get("headline_summary", "")
    categories = bulletin.get("categories", [])
    quiz = bulletin.get("daily_quiz", [])

    chunks = []

    # Chunk 1: Header + Executive Summary
    header_msg = (
        f"🎯 *DAILY CURRENT AFFAIRS BULLETIN*\n"
        f"📅 *Date:* {date}\n"
        f"📚 *Target Focus:* {exam} (SSC / RRB / Bank / UPSC)\n"
        f"{'='*34}\n\n"
        f"⚡ *Executive Briefing:*\n_{headline}_\n\n"
        f"📌 *Sections Included:*\n"
    )
    for cat in categories:
        header_msg += f"• {cat.get('category_name')}\n"
    header_msg += "• Daily 5 Practice MCQs\n"
    chunks.append(header_msg)

    # Category Chunks (group 1-2 categories per message to stay well within 4000 chars)
    current_chunk = ""
    for cat in categories:
        cat_title = cat.get("category_name", "General Affairs")
        cat_text = f"\n🏷️ *{cat_title.upper()}*\n{'-'*30}\n"

        items = cat.get("items", [])
        for idx, item in enumerate(items, 1):
            title = item.get("title", "").strip()
            tag = item.get("exam_tag", "")
            raw_bullets = item.get("summary_bullets", [])
            # Filter out any relevance bullet or empty entries
            filtered_bullets = [
                b.strip() for b in raw_bullets
                if b.strip() and not b.strip().lower().startswith("relevance:")
                and "significant for" not in b.lower()
            ]
            static_info = item.get("static_gk_or_deep_dive", "").strip()
            if static_info.lower().startswith("key static gk:"):
                static_info = static_info[len("key static gk:"):].strip()
            link = item.get("link", "").strip()

            cat_text += f"\n*{idx}. {title}*\n"
            if tag:
                cat_text += f"🔖 _{tag}_\n"
            if filtered_bullets:
                desc_text = " ".join(filtered_bullets)
                cat_text += f"📝 {desc_text}\n"
            if static_info:
                cat_text += f"💡 *Static GK Link:* _{static_info}_\n"
            if link:
                cat_text += f"🔗 [Source Link]({link})\n"

        # Check if adding this category exceeds 3500 chars
        if len(current_chunk) + len(cat_text) > 3500:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = cat_text
        else:
            current_chunk += "\n" + cat_text

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Chunk: Vocab Word of the Day & Static GK Booster
    vocab = bulletin.get("vocab_word")
    booster = bulletin.get("static_gk_booster")
    if vocab or booster:
        extra_msg = ""
        if vocab:
            w = vocab.get("word", "").upper()
            pos = vocab.get("part_of_speech", "")
            meaning = vocab.get("meaning", "")
            syns = ", ".join(vocab.get("synonyms", []))
            ants = ", ".join(vocab.get("antonyms", []))
            ex = vocab.get("example_sentence", "")
            extra_msg += (
                f"📖 *VOCABULARY WORD OF THE DAY (SSC & Banking)*\n"
                f"{'-'*34}\n"
                f"🔤 *{w}* _{f'({pos})' if pos else ''}_\n"
                f"• *Meaning:* {meaning}\n"
            )
            if syns:
                extra_msg += f"• *Synonyms:* {syns}\n"
            if ants:
                extra_msg += f"• *Antonyms:* {ants}\n"
            if ex:
                extra_msg += f"• *Exam Usage:* _{ex}_\n"
            extra_msg += "\n"

        if booster:
            btitle = booster.get("title", "")
            bbullets = booster.get("bullets", [])
            extra_msg += (
                f"🏛️ *STATIC GK BOOSTER*\n"
                f"{'-'*34}\n"
                f"📌 *{btitle}*\n"
            )
            for b in bbullets:
                extra_msg += f"• {b}\n"

        if extra_msg.strip():
            chunks.append(extra_msg.strip())

    # Chunk: Daily Practice Quiz
    if quiz:
        quiz_msg = (
            f"❓ *DAILY EXAM PRACTICE QUIZ (5 MCQs)*\n"
            f"Test your retention from today's current affairs!\n"
            f"{'='*34}\n\n"
        )
        for i, q in enumerate(quiz, 1):
            question = q.get("question", "")
            options = q.get("options", [])
            correct = q.get("correct", "")
            explanation = q.get("explanation", "")

            quiz_msg += f"*{question}*\n"
            for opt in options:
                quiz_msg += f"{opt}\n"
            # Use Telegram spoiler format || ... || so answer isn't spoiled
            quiz_msg += f"👉 *Answer:* ||Option {correct}||\n"
            quiz_msg += f"💡 *Explanation:* _{explanation}_\n\n"

        chunks.append(quiz_msg.strip())

    return chunks


def format_gmail_html(bulletin: Dict) -> str:
    """
    Generates a modern, responsive HTML email template for Gmail.
    Includes dark-mode support, beautiful typography, cards, and quiz sections.
    """
    date = bulletin.get("date", "")
    exam = bulletin.get("exam_type", "ALL")
    headline = bulletin.get("headline_summary", "")
    categories = bulletin.get("categories", [])
    quiz = bulletin.get("daily_quiz", [])

    categories_html = ""
    for cat in categories:
        cat_name = cat.get("category_name", "General Affairs")
        items_html = ""
        items = cat.get("items", [])
        for idx, item in enumerate(items, 1):
            title = item.get("title", "").strip()
            tag = item.get("exam_tag", "")
            raw_bullets = item.get("summary_bullets", [])
            filtered_bullets = [
                b.strip() for b in raw_bullets
                if b.strip() and not b.strip().lower().startswith("relevance:")
                and "significant for" not in b.lower()
            ]
            bullets_li = "".join([f"<li style='margin-bottom: 6px;'>{b}</li>" for b in filtered_bullets])
            desc_html = f"<ul style='margin: 0; padding-left: 20px; color: #475569; font-size: 14px; line-height: 1.5;'>{bullets_li}</ul>" if filtered_bullets else ""

            static_info = item.get("static_gk_or_deep_dive", "").strip()
            if static_info.lower().startswith("key static gk:"):
                static_info = static_info[len("key static gk:"):].strip()

            static_section = ""
            if static_info:
                static_section = f"""
                <div style="background-color: #f1f5f9; padding: 8px 12px; border-radius: 6px; margin-top: 8px; font-size: 13px; color: #334155; border-left: 3px solid #0284c7;">
                    <strong>💡 Static GK / Core Concept:</strong> {static_info}
                </div>
                """
            source_link = ""
            if item.get("link"):
                source_link = f"<div style='margin-top: 6px;'><a href='{item.get('link')}' target='_blank' style='color: #2563eb; text-decoration: none; font-size: 12px;'>🔗 View Official Source &rarr;</a></div>"

            items_html += f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                    <h3 style="margin: 0; font-size: 16px; color: #0f172a; line-height: 1.4;">{idx}. {title}</h3>
                </div>
                <div style="margin-bottom: 10px;">
                    <span style="background-color: #e0e7ff; color: #3730a3; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                        {tag or 'Current Affairs'}
                    </span>
                </div>
                {desc_html}
                {static_section}
                {source_link}
            </div>
            """

        categories_html += f"""
        <div style="margin-bottom: 28px;">
            <h2 style="font-size: 18px; color: #1e293b; border-bottom: 2px solid #3b82f6; padding-bottom: 6px; margin-bottom: 16px;">
                📌 {cat_name}
            </h2>
            {items_html}
        </div>
        """

    quiz_html = ""
    if quiz:
        questions_html = ""
        for i, q in enumerate(quiz, 1):
            options_li = "".join([f"<li style='margin-bottom: 4px;'>{opt}</li>" for opt in q.get("options", [])])
            questions_html += f"""
            <div style="background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                <p style="margin: 0 0 8px 0; font-weight: 600; color: #0f172a; font-size: 14px;">{q.get('question')}</p>
                <ul style="list-style-type: none; padding-left: 0; margin: 0 0 10px 0; font-size: 13px; color: #334155;">
                    {options_li}
                </ul>
                <details style="background: #f8fafc; padding: 8px 12px; border-radius: 6px; border: 1px dashed #94a3b8; font-size: 13px;">
                    <summary style="cursor: pointer; font-weight: bold; color: #0284c7;">Click to reveal Answer & Explanation</summary>
                    <div style="margin-top: 6px; color: #166534;">
                        <strong>Correct Answer:</strong> Option {q.get('correct')}<br/>
                        <span style="color: #475569;"><strong>Explanation:</strong> {q.get('explanation')}</span>
                    </div>
                </details>
            </div>
            """
        quiz_html = f"""
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 20px; margin-top: 30px;">
            <h2 style="margin: 0 0 4px 0; color: #1e40af; font-size: 18px;">🎯 Daily 5 Practice MCQs</h2>
            <p style="margin: 0 0 16px 0; font-size: 13px; color: #64748b;">Test your retention for {exam} exams right away:</p>
            {questions_html}
        </div>
        """

    # Vocab Word of the Day
    vocab = bulletin.get("vocab_word")
    vocab_html = ""
    if vocab:
        w = vocab.get("word", "").upper()
        pos = vocab.get("part_of_speech", "")
        meaning = vocab.get("meaning", "")
        syns = ", ".join(vocab.get("synonyms", []))
        ants = ", ".join(vocab.get("antonyms", []))
        ex = vocab.get("example_sentence", "")
        vocab_html = f"""
        <div style="background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%); border: 1px solid #f0abfc; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 18px; margin-right: 8px;">📖</span>
                <h3 style="margin: 0; color: #86198f; font-size: 16px;">Editorial Vocab Word of the Day (SSC & Banking)</h3>
            </div>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #f5d0fe;">
                <div style="margin-bottom: 6px;">
                    <strong style="font-size: 18px; color: #701a75; letter-spacing: 0.5px;">{w}</strong>
                    <span style="background: #fdf2f8; color: #be185d; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px; font-weight: 600;">{pos}</span>
                </div>
                <p style="margin: 0 0 8px 0; color: #374151; font-size: 14px; line-height: 1.5;"><strong>Meaning:</strong> {meaning}</p>
                {f'<p style="margin: 0 0 6px 0; font-size: 13px; color: #4b5563;"><strong>Synonyms:</strong> {syns}</p>' if syns else ''}
                {f'<p style="margin: 0 0 6px 0; font-size: 13px; color: #4b5563;"><strong>Antonyms:</strong> {ants}</p>' if ants else ''}
                {f'<p style="margin: 0; font-size: 13px; color: #6b7280; font-style: italic;"><strong>Exam Usage:</strong> "{ex}"</p>' if ex else ''}
            </div>
        </div>
        """

    # Static GK Booster
    booster = bulletin.get("static_gk_booster")
    booster_html = ""
    if booster:
        btitle = booster.get("title", "")
        bbullets = "".join([f"<li style='margin-bottom: 6px;'>{b}</li>" for b in booster.get("bullets", [])])
        booster_html = f"""
        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 1px solid #a7f3d0; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 18px; margin-right: 8px;">🏛️</span>
                <h3 style="margin: 0; color: #065f46; font-size: 16px;">Daily Static GK Booster</h3>
            </div>
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #a7f3d0;">
                <h4 style="margin: 0 0 8px 0; font-size: 15px; color: #047857;">📌 {btitle}</h4>
                <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 13.5px; line-height: 1.5;">
                    {bbullets}
                </ul>
            </div>
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Current Affairs - {date}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
    <div style="max-width: 680px; margin: 0 auto; padding: 24px 16px;">
        
        <!-- Header Banner -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); border-radius: 14px; padding: 24px; text-align: center; color: #ffffff; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px;">
                EXAM FOCUS: {exam}
            </div>
            <h1 style="margin: 0 0 6px 0; font-size: 24px; font-weight: 700;">Daily Current Affairs Digest</h1>
            <p style="margin: 0; font-size: 14px; opacity: 0.9;">📅 {date} | Tailored for SSC, RRB, Banking & UPSC</p>
        </div>

        <!-- Executive Briefing -->
        <div style="background-color: #ffffff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 16px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
            <h3 style="margin: 0 0 6px 0; font-size: 14px; text-transform: uppercase; color: #2563eb; letter-spacing: 0.5px;">⚡ Executive Briefing</h3>
            <p style="margin: 0; font-size: 15px; line-height: 1.5; color: #334155; font-weight: 500;">
                {headline}
            </p>
        </div>

        <!-- Categories and News -->
        {categories_html}

        <!-- Vocab Word of the Day -->
        {vocab_html}

        <!-- Static GK Booster -->
        {booster_html}

        <!-- Daily Quiz Section -->
        {quiz_html}

        <!-- Footer -->
        <div style="text-align: center; margin-top: 36px; padding-top: 20px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
            <p style="margin: 0 0 6px 0;">✨ <em>"Consistency is the key to cracking competitive exams."</em></p>
            <p style="margin: 0;">Automated Daily Dispatch via Exam Current Affairs Agent &bull; Press Information Bureau &bull; The Hindu &bull; National Wire</p>
        </div>
    </div>
</body>
</html>
"""
    return full_html


def format_plain_text(bulletin: Dict) -> str:
    """Generates plain text format for console or fallback."""
    date = bulletin.get("date", "")
    exam = bulletin.get("exam_type", "ALL")
    headline = bulletin.get("headline_summary", "")
    categories = bulletin.get("categories", [])
    quiz = bulletin.get("daily_quiz", [])

    lines = [
        f"DAILY CURRENT AFFAIRS BULLETIN - {date}",
        f"Focus: {exam}",
        "=" * 60,
        f"BRIEFING: {headline}",
        "=" * 60,
        ""
    ]

    for cat in categories:
        lines.append(f"\n[{cat.get('category_name', '').upper()}]")
        lines.append("-" * 40)
        items = cat.get("items", [])
        for idx, item in enumerate(items, 1):
            lines.append(f"\n{idx}. {item.get('title')}")
            if item.get("exam_tag"):
                lines.append(f"   Tag: {item.get('exam_tag')}")
            raw_bullets = item.get("summary_bullets", [])
            filtered_bullets = [
                b.strip() for b in raw_bullets
                if b.strip() and not b.strip().lower().startswith("relevance:")
                and "significant for" not in b.lower()
            ]
            for b in filtered_bullets:
                lines.append(f"   - {b}")
            static_info = item.get("static_gk_or_deep_dive", "").strip()
            if static_info.lower().startswith("key static gk:"):
                static_info = static_info[len("key static gk:"):].strip()
            if static_info:
                lines.append(f"   Static GK: {static_info}")
            if item.get("link"):
                lines.append(f"   Source: {item.get('link')}")

    vocab = bulletin.get("vocab_word")
    if vocab:
        w = vocab.get("word", "").upper()
        pos = vocab.get("part_of_speech", "")
        lines.append("\n" + "=" * 60)
        lines.append(f"VOCABULARY WORD OF THE DAY: {w} ({pos})")
        lines.append("=" * 60)
        lines.append(f"Meaning: {vocab.get('meaning', '')}")
        if vocab.get("synonyms"):
            lines.append(f"Synonyms: {', '.join(vocab.get('synonyms'))}")
        if vocab.get("antonyms"):
            lines.append(f"Antonyms: {', '.join(vocab.get('antonyms'))}")
        if vocab.get("example_sentence"):
            lines.append(f"Usage: {vocab.get('example_sentence')}")

    booster = bulletin.get("static_gk_booster")
    if booster:
        lines.append("\n" + "=" * 60)
        lines.append(f"STATIC GK BOOSTER: {booster.get('title', '')}")
        lines.append("=" * 60)
        for b in booster.get("bullets", []):
            lines.append(f"- {b}")

    if quiz:
        lines.append("\n" + "=" * 60)
        lines.append("DAILY PRACTICE QUIZ")
        lines.append("=" * 60)
        for q in quiz:
            lines.append(f"\n{q.get('question')}")
            for opt in q.get("options", []):
                lines.append(f"  {opt}")
            lines.append(f"  Correct Answer: Option {q.get('correct')}")
            lines.append(f"  Explanation: {q.get('explanation')}")

    return "\n".join(lines)
