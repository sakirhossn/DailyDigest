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
    source = bulletin.get("content_source", "unknown")
    source_label = "🤖 Gemini AI" if source == "gemini" else ("⚠️ Fallback Engine" if source == "fallback" else "Unknown")

    header_msg = (
        f"🎯 *DAILY CURRENT AFFAIRS BULLETIN*\n"
        f"📅 *Date:* {date}\n"
        f"📚 *Target Focus:* {exam} (SSC / RRB / Bank / UPSC)\n"
        f"🔎 *Content Source:* {source_label}\n"
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

    # Chunk(s): Vocab Words / Idioms of the Day & Static GK Boosters (5 each)
    vocab_list = bulletin.get("vocab_words") or ([bulletin["vocab_word"]] if bulletin.get("vocab_word") else [])
    idiom_list = bulletin.get("idioms_of_the_day") or ([bulletin["idiom_of_the_day"]] if bulletin.get("idiom_of_the_day") else [])
    booster_list = bulletin.get("static_gk_boosters") or ([bulletin["static_gk_booster"]] if bulletin.get("static_gk_booster") else [])

    if vocab_list:
        vocab_msg = f"📖 *VOCABULARY WORDS OF THE DAY (SSC & Banking)*\n{'='*34}\n\n"
        for n, vocab in enumerate(vocab_list, 1):
            w = vocab.get("word", "").upper()
            pos = vocab.get("part_of_speech", "")
            meaning = vocab.get("meaning", "")
            syns = ", ".join(vocab.get("synonyms", []))
            ants = ", ".join(vocab.get("antonyms", []))
            ex = vocab.get("example_sentence", "")
            vocab_msg += (
                f"🔤 *{n}. {w}* _{f'({pos})' if pos else ''}_\n"
                f"• *Meaning:* {meaning}\n"
            )
            if syns:
                vocab_msg += f"• *Synonyms:* {syns}\n"
            if ants:
                vocab_msg += f"• *Antonyms:* {ants}\n"
            if ex:
                vocab_msg += f"• *Exam Usage:* _{ex}_\n"
            vocab_msg += "\n"
        chunks.append(vocab_msg.strip())

    if idiom_list:
        idiom_msg = f"🗣️ *IDIOMS OF THE DAY*\n{'='*34}\n\n"
        for n, idiom in enumerate(idiom_list, 1):
            i_text = idiom.get("idiom", "")
            i_meaning = idiom.get("meaning", "")
            i_ex = idiom.get("example_sentence", "")
            idiom_msg += (
                f"💬 *{n}. {i_text}*\n"
                f"• *Meaning:* {i_meaning}\n"
            )
            if i_ex:
                idiom_msg += f"• *Usage:* _{i_ex}_\n"
            idiom_msg += "\n"
        chunks.append(idiom_msg.strip())

    if booster_list:
        booster_msg = f"🏛️ *STATIC GK BOOSTERS*\n{'='*34}\n\n"
        for n, booster in enumerate(booster_list, 1):
            btitle = booster.get("title", "")
            bbullets = booster.get("bullets", [])
            booster_msg += f"📌 *{n}. {btitle}*\n"
            for b in bbullets:
                booster_msg += f"• {b}\n"
            booster_msg += "\n"
        chunks.append(booster_msg.strip())

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

    source = bulletin.get("content_source", "unknown")
    if source == "gemini":
        source_label, source_bg = "🤖 Gemini AI", "rgba(255, 255, 255, 0.2)"
    elif source == "fallback":
        source_label, source_bg = "⚠️ Fallback Engine", "rgba(251, 191, 36, 0.35)"
    else:
        source_label, source_bg = "Unknown Source", "rgba(255, 255, 255, 0.2)"

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

    # Vocab Words of the Day (up to 5)
    vocab_list = bulletin.get("vocab_words") or ([bulletin["vocab_word"]] if bulletin.get("vocab_word") else [])
    vocab_html = ""
    if vocab_list:
        vocab_cards = ""
        for vocab in vocab_list:
            w = vocab.get("word", "").upper()
            pos = vocab.get("part_of_speech", "")
            meaning = vocab.get("meaning", "")
            syns = ", ".join(vocab.get("synonyms", []))
            ants = ", ".join(vocab.get("antonyms", []))
            ex = vocab.get("example_sentence", "")
            vocab_cards += f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #f5d0fe; margin-bottom: 10px;">
                <div style="margin-bottom: 6px;">
                    <strong style="font-size: 18px; color: #701a75; letter-spacing: 0.5px;">{w}</strong>
                    <span style="background: #fdf2f8; color: #be185d; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 8px; font-weight: 600;">{pos}</span>
                </div>
                <p style="margin: 0 0 8px 0; color: #374151; font-size: 14px; line-height: 1.5;"><strong>Meaning:</strong> {meaning}</p>
                {f'<p style="margin: 0 0 6px 0; font-size: 13px; color: #4b5563;"><strong>Synonyms:</strong> {syns}</p>' if syns else ''}
                {f'<p style="margin: 0 0 6px 0; font-size: 13px; color: #4b5563;"><strong>Antonyms:</strong> {ants}</p>' if ants else ''}
                {f'<p style="margin: 0; font-size: 13px; color: #6b7280; font-style: italic;"><strong>Exam Usage:</strong> "{ex}"</p>' if ex else ''}
            </div>
            """
        vocab_html = f"""
        <div style="background: linear-gradient(135deg, #fdf4ff 0%, #fae8ff 100%); border: 1px solid #f0abfc; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 18px; margin-right: 8px;">📖</span>
                <h3 style="margin: 0; color: #86198f; font-size: 16px;">Editorial Vocab Words of the Day (SSC & Banking)</h3>
            </div>
            {vocab_cards}
        </div>
        """

    # Idioms of the Day (up to 5, same layout family as Vocab cards, amber theme)
    idiom_list = bulletin.get("idioms_of_the_day") or ([bulletin["idiom_of_the_day"]] if bulletin.get("idiom_of_the_day") else [])
    idiom_html = ""
    if idiom_list:
        idiom_cards = ""
        for idiom in idiom_list:
            i_text = idiom.get("idiom", "")
            i_meaning = idiom.get("meaning", "")
            i_ex = idiom.get("example_sentence", "")
            idiom_cards += f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #fde68a; margin-bottom: 10px;">
                <div style="margin-bottom: 6px;">
                    <strong style="font-size: 18px; color: #78350f; letter-spacing: 0.3px;">{i_text}</strong>
                </div>
                <p style="margin: 0 0 8px 0; color: #374151; font-size: 14px; line-height: 1.5;"><strong>Meaning:</strong> {i_meaning}</p>
                {f'<p style="margin: 0; font-size: 13px; color: #6b7280; font-style: italic;"><strong>Usage:</strong> "{i_ex}"</p>' if i_ex else ''}
            </div>
            """
        idiom_html = f"""
        <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #fde68a; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 18px; margin-right: 8px;">🗣️</span>
                <h3 style="margin: 0; color: #92400e; font-size: 16px;">Idioms of the Day</h3>
            </div>
            {idiom_cards}
        </div>
        """

    # Static GK Boosters (up to 5)
    booster_list = bulletin.get("static_gk_boosters") or ([bulletin["static_gk_booster"]] if bulletin.get("static_gk_booster") else [])
    booster_html = ""
    if booster_list:
        booster_cards = ""
        for booster in booster_list:
            btitle = booster.get("title", "")
            bbullets = "".join([f"<li style='margin-bottom: 6px;'>{b}</li>" for b in booster.get("bullets", [])])
            booster_cards += f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 14px; border: 1px solid #a7f3d0; margin-bottom: 10px;">
                <h4 style="margin: 0 0 8px 0; font-size: 15px; color: #047857;">📌 {btitle}</h4>
                <ul style="margin: 0; padding-left: 20px; color: #374151; font-size: 13.5px; line-height: 1.5;">
                    {bbullets}
                </ul>
            </div>
            """
        booster_html = f"""
        <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 1px solid #a7f3d0; border-radius: 12px; padding: 18px; margin-bottom: 24px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 18px; margin-right: 8px;">🏛️</span>
                <h3 style="margin: 0; color: #065f46; font-size: 16px;">Daily Static GK Boosters</h3>
            </div>
            {booster_cards}
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
            <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px; margin-right: 6px;">
                EXAM FOCUS: {exam}
            </div>
            <div style="display: inline-block; background-color: {source_bg}; padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px;">
                {source_label}
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

        <!-- Idiom of the Day -->
        {idiom_html}

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

    source = bulletin.get("content_source", "unknown")
    source_label = "Gemini AI" if source == "gemini" else ("Fallback Engine" if source == "fallback" else "Unknown")

    lines = [
        f"DAILY CURRENT AFFAIRS BULLETIN - {date}",
        f"Focus: {exam}",
        f"Content Source: {source_label}",
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

    vocab_list = bulletin.get("vocab_words") or ([bulletin["vocab_word"]] if bulletin.get("vocab_word") else [])
    if vocab_list:
        lines.append("\n" + "=" * 60)
        lines.append("VOCABULARY WORDS OF THE DAY")
        lines.append("=" * 60)
        for n, vocab in enumerate(vocab_list, 1):
            w = vocab.get("word", "").upper()
            pos = vocab.get("part_of_speech", "")
            lines.append(f"\n{n}. {w} ({pos})")
            lines.append(f"   Meaning: {vocab.get('meaning', '')}")
            if vocab.get("synonyms"):
                lines.append(f"   Synonyms: {', '.join(vocab.get('synonyms'))}")
            if vocab.get("antonyms"):
                lines.append(f"   Antonyms: {', '.join(vocab.get('antonyms'))}")
            if vocab.get("example_sentence"):
                lines.append(f"   Usage: {vocab.get('example_sentence')}")

    idiom_list = bulletin.get("idioms_of_the_day") or ([bulletin["idiom_of_the_day"]] if bulletin.get("idiom_of_the_day") else [])
    if idiom_list:
        lines.append("\n" + "=" * 60)
        lines.append("IDIOMS OF THE DAY")
        lines.append("=" * 60)
        for n, idiom in enumerate(idiom_list, 1):
            lines.append(f"\n{n}. {idiom.get('idiom', '')}")
            lines.append(f"   Meaning: {idiom.get('meaning', '')}")
            if idiom.get("example_sentence"):
                lines.append(f"   Usage: {idiom.get('example_sentence')}")

    booster_list = bulletin.get("static_gk_boosters") or ([bulletin["static_gk_booster"]] if bulletin.get("static_gk_booster") else [])
    if booster_list:
        lines.append("\n" + "=" * 60)
        lines.append("STATIC GK BOOSTERS")
        lines.append("=" * 60)
        for n, booster in enumerate(booster_list, 1):
            lines.append(f"\n{n}. {booster.get('title', '')}")
            for b in booster.get("bullets", []):
                lines.append(f"   - {b}")

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


def format_revision_digest_html(entries: List[Dict], start_date: str, end_date: str) -> str:
    """
    Compiles the last N days of vocab words, idioms, and static GK boosters
    (from processors/curator.py's revision_log.json) into a single HTML email,
    grouped by day, reusing the same card styles as the daily digest.
    """
    days_html = ""
    for entry in entries:
        day_date = entry.get("date", "")
        vocab_list = entry.get("vocab_words", [])
        idiom_list = entry.get("idioms_of_the_day", [])
        booster_list = entry.get("static_gk_boosters", [])

        vocab_cards = "".join([f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 12px; border: 1px solid #f5d0fe; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: #701a75;">{v.get('word','').upper()}</strong>
                <span style="background: #fdf2f8; color: #be185d; padding: 2px 6px; border-radius: 8px; font-size: 10px; margin-left: 6px; font-weight: 600;">{v.get('part_of_speech','')}</span>
                <p style="margin: 4px 0 0 0; color: #374151; font-size: 13px; line-height: 1.4;">{v.get('meaning','')}</p>
            </div>
        """ for v in vocab_list])

        idiom_cards = "".join([f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 12px; border: 1px solid #fde68a; margin-bottom: 8px;">
                <strong style="font-size: 15px; color: #78350f;">{i.get('idiom','')}</strong>
                <p style="margin: 4px 0 0 0; color: #374151; font-size: 13px; line-height: 1.4;">{i.get('meaning','')}</p>
            </div>
        """ for i in idiom_list])

        booster_cards = "".join([f"""
            <div style="background: #ffffff; border-radius: 8px; padding: 12px; border: 1px solid #a7f3d0; margin-bottom: 8px;">
                <strong style="font-size: 14px; color: #047857;">📌 {b.get('title','')}</strong>
                <ul style="margin: 4px 0 0 0; padding-left: 18px; color: #374151; font-size: 12.5px; line-height: 1.4;">
                    {"".join([f"<li>{bullet}</li>" for bullet in b.get('bullets', [])])}
                </ul>
            </div>
        """ for b in booster_list])

        days_html += f"""
        <div style="margin-bottom: 26px;">
            <h3 style="font-size: 14px; color: #1e293b; border-bottom: 2px solid #cbd5e1; padding-bottom: 6px; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px;">
                🗓️ {day_date}
            </h3>
            {vocab_cards}
            {idiom_cards}
            {booster_cards}
        </div>
        """

    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>10-Day Revision Digest</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
    <div style="max-width: 680px; margin: 0 auto; padding: 24px 16px;">

        <div style="background: linear-gradient(135deg, #6d28d9 0%, #a855f7 100%); border-radius: 14px; padding: 24px; text-align: center; color: #ffffff; margin-bottom: 28px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="display: inline-block; background-color: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 16px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 8px;">
                10-DAY REVISION CHECKPOINT
            </div>
            <h1 style="margin: 0 0 6px 0; font-size: 22px; font-weight: 700;">Vocab, Idioms &amp; Static GK Revision</h1>
            <p style="margin: 0; font-size: 13px; opacity: 0.9;">📅 {start_date} &rarr; {end_date}</p>
        </div>

        {days_html}

        <div style="text-align: center; margin-top: 30px; padding-top: 18px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8;">
            <p style="margin: 0;">✨ <em>"Revision is where retention actually happens — review these before moving on."</em></p>
        </div>
    </div>
</body>
</html>
"""
    return full_html


def format_revision_digest_plain(entries: List[Dict], start_date: str, end_date: str) -> str:
    """Plain-text fallback version of the 10-day revision digest."""
    lines = [
        f"10-DAY REVISION DIGEST: {start_date} to {end_date}",
        "=" * 60,
        ""
    ]
    for entry in entries:
        lines.append(f"\n[{entry.get('date', '')}]")
        lines.append("-" * 40)
        for v in entry.get("vocab_words", []):
            lines.append(f"  VOCAB: {v.get('word','').upper()} ({v.get('part_of_speech','')}) - {v.get('meaning','')}")
        for i in entry.get("idioms_of_the_day", []):
            lines.append(f"  IDIOM: {i.get('idiom','')} - {i.get('meaning','')}")
        for b in entry.get("static_gk_boosters", []):
            lines.append(f"  GK: {b.get('title','')}")
            for bullet in b.get("bullets", []):
                lines.append(f"      - {bullet}")

    return "\n".join(lines)


def format_revision_digest_pdf_html(entries: List[Dict], start_date: str, end_date: str) -> str:
    """
    A SIMPLIFIED HTML template for the 10-day revision digest, used only for PDF
    generation via xhtml2pdf. Avoids CSS gradients/flexbox/box-shadow, which
    xhtml2pdf's ReportLab-based renderer does not support well — uses solid
    colors and simple block/table layout instead so the PDF renders cleanly.
    The email BODY still uses format_revision_digest_html() (full styling);
    this one is only for the PDF attachment.
    """
    days_html = ""
    for entry in entries:
        day_date = entry.get("date", "")
        vocab_list = entry.get("vocab_words", [])
        idiom_list = entry.get("idioms_of_the_day", [])
        booster_list = entry.get("static_gk_boosters", [])

        vocab_rows = "".join([f"""
            <div style="background-color: #fdf4ff; border: 1px solid #e9a8f2; padding: 10px; margin-bottom: 6px;">
                <b style="color: #701a75; font-size: 13px;">{v.get('word','').upper()}</b>
                <span style="color: #be185d; font-size: 10px;"> ({v.get('part_of_speech','')})</span><br/>
                <span style="color: #374151; font-size: 11px;">{v.get('meaning','')}</span>
            </div>
        """ for v in vocab_list])

        idiom_rows = "".join([f"""
            <div style="background-color: #fffbeb; border: 1px solid #f5cf6b; padding: 10px; margin-bottom: 6px;">
                <b style="color: #78350f; font-size: 13px;">{i.get('idiom','')}</b><br/>
                <span style="color: #374151; font-size: 11px;">{i.get('meaning','')}</span>
            </div>
        """ for i in idiom_list])

        booster_rows = "".join([f"""
            <div style="background-color: #ecfdf5; border: 1px solid #86e0b8; padding: 10px; margin-bottom: 6px;">
                <b style="color: #047857; font-size: 12px;">{b.get('title','')}</b>
                <ul style="margin: 4px 0 0 0; padding-left: 16px; color: #374151; font-size: 10.5px;">
                    {"".join([f"<li>{bullet}</li>" for bullet in b.get('bullets', [])])}
                </ul>
            </div>
        """ for b in booster_list])

        days_html += f"""
        <div style="margin-bottom: 18px;">
            <div style="background-color: #e2e8f0; padding: 6px 10px; font-size: 12px; font-weight: bold; color: #1e293b; margin-bottom: 8px;">
                {day_date}
            </div>
            {vocab_rows}
            {idiom_rows}
            {booster_rows}
        </div>
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: Helvetica, Arial, sans-serif; color: #1e293b; }}
</style>
</head>
<body>
    <div style="background-color: #6d28d9; padding: 16px; text-align: center; color: #ffffff; margin-bottom: 20px;">
        <div style="font-size: 11px; letter-spacing: 1px;">10-DAY REVISION CHECKPOINT</div>
        <div style="font-size: 18px; font-weight: bold; margin-top: 6px;">Vocab, Idioms &amp; Static GK Revision</div>
        <div style="font-size: 11px; margin-top: 4px;">{start_date} to {end_date}</div>
    </div>
    {days_html}
</body>
</html>
"""
