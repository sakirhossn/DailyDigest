"""
Curator for Daily Current Affairs Agent.
Transforms raw news items into structured, exam-oriented bulletins (UPSC, Bank, SSC, RRB).
Uses Google Gemini API when configured, with a smart heuristic fallback engine.
"""

import datetime
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GEMINI_API_KEY, GEMINI_MODEL, TARGET_EXAM

logger = logging.getLogger(__name__)

EXAM_INSTRUCTIONS = {
    "UPSC": (
        "Focus on Civil Services (CSE) syllabus: GS-1 (Geography, History, Society), "
        "GS-2 (Polity, Governance, Constitution, IR, Welfare Schemes), "
        "GS-3 (Economy, Agriculture, Science & Tech, Environment, Internal Security), "
        "and GS-4 (Ethics/Values in governance). Emphasize constitutional provisions, "
        "supreme court judgments, committee recommendations, environmental conventions, "
        "and balanced analytical perspectives with Prelims facts + Mains angles."
    ),
    "BANK": (
        "Focus on Banking & Financial Awareness (IBPS PO/Clerk, SBI PO, RBI Grade B): "
        "RBI circulars, repo/reverse repo rates, monetary policy committee (MPC), "
        "banking mergers, NPAs, regulatory guidelines, GDP growth projections (IMF, World Bank, ADB, RBI), "
        "financial tech (UPI, CBDC), MoUs, national appointments of bank chiefs, and economic indicators."
    ),
    "SSC": (
        "Focus on SSC (CGL, CHSL, MTS, CPO) General Awareness: Crisp one-liner facts, "
        "latest appointments (Govt, Armed forces, Chief Justices, Commissions), "
        "national and international awards (Padma, Nobel, Sports awards), summits & venues, "
        "military exercises & partner countries, government portals/apps, and static GK links "
        "(capital, currency, headquarters, national parks, articles of constitution)."
    ),
    "RRB": (
        "Focus on Railway Recruitment Board exams (NTPC, Group D, ALP): "
        "Indian Railways developments (new tracks, Vande Bharat, Kavach anti-collision, electrification), "
        "General Science in everyday life, national appointments, major sports wins, "
        "important days & themes, awards, and basic static GK."
    ),
    "ALL": (
        "Provide a comprehensive, multi-exam current affairs digest balancing deep analytical "
        "points for UPSC/State PSC, crucial financial/banking updates for Banking exams, "
        "and crisp one-liners, appointments, awards, and sports for SSC & RRB aspirants."
    ),
}


def build_gemini_prompt(articles: List[Dict], exam_type: str, today_str: str) -> str:
    """Builds a structured prompt for Gemini to process current affairs."""
    exam_guide = EXAM_INSTRUCTIONS.get(exam_type, EXAM_INSTRUCTIONS["ALL"])

    # Prepare top 25 candidate news items for context
    news_corpus = []
    for i, a in enumerate(articles[:25], 1):
        news_corpus.append(
            f"[{i}] Category: {a.get('category')}\n"
            f"Title: {a.get('title')}\n"
            f"Summary: {a.get('summary')[:300]}\n"
            f"Source URL: {a.get('link')}"
        )
    news_text = "\n\n".join(news_corpus)

    return f"""You are an expert faculty and current affairs editor specializing in Indian competitive exams (UPSC, Banking, SSC, RRB).
Today's Date: {today_str}
Target Exam Profile: {exam_type}
Guideline for this Exam: {exam_guide}

Here are today's verified news articles:
{news_text}

Analyze, filter, and curate the most exam-relevant stories into a structured JSON response.
Do NOT include fluff, local crime, or purely political campaign squabbles. Focus strictly on topics tested in government exams.

Produce a strictly valid JSON object matching this schema:
{{
  "date": "{today_str}",
  "exam_type": "{exam_type}",
  "headline_summary": "1-2 sentence executive briefing of today's most important national/economic development.",
  "categories": [
    {{
      "category_name": "Category Name (e.g. Polity & Governance / Economy & Banking / Sci-Tech & Defence / Government Schemes / Sports & Awards)",
      "items": [
        {{
          "title": "Clear, informative headline",
          "summary_bullets": [
            "Key fact / development",
            "Why it matters / exam significance"
          ],
          "exam_tag": "e.g. GS-2 Polity / Banking Awareness / SSC One-Liner",
          "static_gk_or_deep_dive": "Relevant static GK fact or constitutional article / banking term / headquarters",
          "link": "Source URL from the input articles if available"
        }}
      ]
    }}
  ],
  "vocab_word": {
    "word": "EXAM_VOCAB_WORD (high-frequency editorial word relevant for SSC & Bank English)",
    "part_of_speech": "Adjective/Noun/Verb",
    "meaning": "Clear, concise definition",
    "synonyms": ["synonym 1", "synonym 2", "synonym 3"],
    "antonyms": ["antonym 1", "antonym 2"],
    "example_sentence": "An exam-grade sentence demonstrating its usage."
  },
  "static_gk_booster": {
    "title": "Topic in Today's News (e.g. Kaziranga National Park / Monetary Policy Committee / Election Commission / Ramsar Sites)",
    "bullets": [
      "Key constitutional / legal basis or founding year",
      "Geographical location, associated river, or institutional headquarters",
      "Important exam trivia frequently asked in SSC/Banking/UPSC"
    ]
  },
  "daily_quiz": [
    {{
      "question": "Exam-level multiple choice question based on today's news",
      "options": [
        "A) Option 1",
        "B) Option 2",
        "C) Option 3",
        "D) Option 4"
      ],
      "correct": "A/B/C/D",
      "explanation": "Crisp explanation explaining why the answer is correct and its exam relevance."
    }}
  ]
}}

Provide 4 to 6 categories with 2-3 high-yield items each.
Provide exactly 1 high-yield vocab_word.
Provide exactly 1 static_gk_booster.
Provide exactly 5 high-quality exam MCQs in daily_quiz.
Respond ONLY with the JSON object. Do not include markdown code backticks around the json if possible, or use standard ```json ... ```.
"""


def curate_news_with_gemini(articles: List[Dict], exam_type: str, api_key: str) -> Optional[Dict]:
    """Uses Google GenAI SDK to curate and structure current affairs."""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        today_str = datetime.date.today().strftime("%d %B %Y")
        prompt = build_gemini_prompt(articles, exam_type, today_str)

        logger.info(f"Calling Gemini ({GEMINI_MODEL}) for {exam_type} curation...")
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        response_text = response.text.strip()
        # Clean any markdown code blocks
        if response_text.startswith("```"):
            response_text = re.sub(r"^```(?:json)?\n", "", response_text)
            response_text = re.sub(r"\n```$", "", response_text)

        bulletin_data = json.loads(response_text)
        logger.info(f"Successfully generated Gemini bulletin with {len(bulletin_data.get('categories', []))} categories and {len(bulletin_data.get('daily_quiz', []))} MCQs.")
        return bulletin_data

    except Exception as e:
        logger.error(f"Gemini curation failed: {e}. Falling back to heuristic engine.")
        return None


def curate_news_heuristic(articles: List[Dict], exam_type: str) -> Dict:
    """
    Intelligent rule-based fallback when Gemini API key is not supplied or offline.
    Categorizes news based on domain keywords and generates practice MCQs.
    """
    today_str = datetime.date.today().strftime("%d %B %Y")
    logger.info(f"Using heuristic curator for exam type: {exam_type}")

    # Exam filtering keywords
    keywords_map = {
        "Polity, Governance & National": ["cabinet", "bill", "court", "parliament", "constitution", "article", "ladakh", "tribal", "commission", "scheme", "ministry"],
        "Economy & Banking Awareness": ["rbi", "bank", "inflation", "gdp", "rupee", "sebi", "fiscal", "monetary", "repo", "export", "trade", "tax", "gst", "growth"],
        "Defence, Science & Space": ["isro", "drdo", "missile", "satellite", "defence", "exercise", "navy", "army", "ai", "technology", "space"],
        "International Relations & Summits": ["summit", "bilateral", "un", "treaty", "g20", "brics", "asean", "minister", "foreign", "envoy"],
        "Sports, Awards & Appointments": ["appointed", "award", "medal", "champion", "olympic", "cricket", "president", "director", "honour", "fellowship"]
    }

    categorized: Dict[str, List[Dict]] = {k: [] for k in keywords_map}
    other_items = []

    for article in articles:
        text = (article["title"] + " " + article["summary"]).lower()
        matched = False
        for cat, kws in keywords_map.items():
            if any(kw in text for kw in kws):
                categorized[cat].append(article)
                matched = True
                break
        if not matched:
            other_items.append(article)

    # Pick top items per category
    bulletin_categories = []
    for cat_name, cat_articles in categorized.items():
        if not cat_articles:
            continue
        items = []
        for a in cat_articles[:3]:
            # Clean static info without repeated prefix
            if "Polity" in cat_name:
                tag = "UPSC GS-2 / SSC Polity"
                static_info = "Relevant Articles of the Constitution, concerned Ministry and statutory bodies."
            elif "Economy" in cat_name:
                tag = "Bank Awareness / UPSC GS-3"
                static_info = "RBI Act 1934, Monetary Policy Committee (MPC) framework, and banking concepts."
            elif "Defence" in cat_name:
                tag = "Defence & Tech (SSC / UPSC / RRB)"
                static_info = "ISRO/DRDO Headquarters, command hierarchy, and technology specifications."
            elif "International" in cat_name:
                tag = "UPSC GS-2 / International Summits"
                static_info = "Member states, capitals, currencies, and multilateral groupings (UN, G20, BRICS)."
            else:
                tag = "SSC / RRB / Static GK"
                static_info = "Headquarters, governing bodies, and static achievements."

            summary_text = (a.get("summary") or "").strip()
            # If summary is too short or empty, provide a clean fallback
            if len(summary_text) < 20:
                summary_text = a["title"]

            items.append({
                "title": a["title"],
                "summary_bullets": [
                    summary_text[:280] + "..." if len(summary_text) > 280 else summary_text
                ],
                "exam_tag": tag,
                "static_gk_or_deep_dive": static_info,
                "link": a["link"]
            })

        if items:
            bulletin_categories.append({
                "category_name": cat_name,
                "items": items
            })

    # Heuristic MCQs from top articles
    quiz = []
    top_picks = articles[:5]
    for i, a in enumerate(top_picks, 1):
        quiz.append({
            "question": f"Q{i}. Regarding the recent development: '{a['title']}', which of the following is correct?",
            "options": [
                f"A) It pertains directly to {a.get('category', 'National Affairs')}",
                "B) It was rejected by the concerned ministry",
                "C) It is only applicable to non-governmental organizations",
                "D) None of the above"
            ],
            "correct": "A",
            "explanation": f"Based on the official release: {a['summary'][:160]}..."
        })

    # Fallback Vocab Word of the Day (high frequency editorial words)
    sample_vocab = {
        "word": "EXIGENCY",
        "part_of_speech": "Noun",
        "meaning": "An urgent need or demand; an emergency situation requiring immediate action.",
        "synonyms": ["necessity", "urgency", "crisis", "predicament"],
        "antonyms": ["unimportance", "ease", "calm"],
        "example_sentence": "The economic exigency compelled the Finance Ministry to introduce targeted fiscal reforms."
    }

    # Fallback Static GK Booster
    sample_booster = {
        "title": "Monetary Policy Committee (MPC) & RBI Basics",
        "bullets": [
            "Constituted under Section 45ZB of the Reserve Bank of India Act, 1934.",
            "Consists of 6 members: 3 from RBI (including RBI Governor as ex-officio Chairperson) and 3 external members appointed by the Government.",
            "Each member has one vote; the Governor has a casting vote in case of a tie."
        ]
    }

    return {
        "date": today_str,
        "exam_type": exam_type,
        "headline_summary": f"Daily Current Affairs Digest curated specifically for {exam_type} aspirants covering key national, economic, and scientific developments.",
        "categories": bulletin_categories,
        "vocab_word": sample_vocab,
        "static_gk_booster": sample_booster,
        "daily_quiz": quiz
    }


def curate_daily_bulletin(articles: List[Dict], exam_type: str = TARGET_EXAM, api_key: str = GEMINI_API_KEY) -> Dict:
    """Main curation entry point: tries Gemini first, falls back to Heuristic engine."""
    if api_key:
        result = curate_news_with_gemini(articles, exam_type, api_key)
        if result:
            return result

    return curate_news_heuristic(articles, exam_type)
