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

# ---------------------------------------------------------------------------
# Cross-run "recently used" tracking, so vocab/idioms/GK boosters don't repeat
# day to day. Stored alongside the committed docs/archive/ folder so it
# persists across workflow runs (the workflow already commits that folder).
# ---------------------------------------------------------------------------
USED_CONTENT_PATH = Path(__file__).resolve().parent.parent / "docs" / "archive" / "used_content.json"
USED_CONTENT_CAP = 60  # keep roughly the last ~2 months of history per category

# Full daily vocab/idiom/GK content (not just identifiers) for the 10-day revision digest.
REVISION_LOG_PATH = Path(__file__).resolve().parent.parent / "docs" / "archive" / "revision_log.json"
REVISION_LOG_CAP = 200  # keep plenty of history; revision_digest.py only reads the last 10


def load_used_content() -> Dict[str, List[str]]:
    """Loads the rolling history of recently used vocab/idiom/GK identifiers."""
    try:
        if USED_CONTENT_PATH.exists():
            with open(USED_CONTENT_PATH, "r", encoding="utf-8") as fh:
                data = json.load(fh)
                return {
                    "vocab": data.get("vocab", []),
                    "idiom": data.get("idiom", []),
                    "gk_booster": data.get("gk_booster", []),
                }
    except Exception as e:
        logger.warning(f"Could not load used_content.json, starting fresh: {e}")
    return {"vocab": [], "idiom": [], "gk_booster": []}


def save_used_content(used: Dict[str, List[str]]) -> None:
    """Persists the (capped) rolling history back to disk."""
    try:
        USED_CONTENT_PATH.parent.mkdir(parents=True, exist_ok=True)
        capped = {k: v[-USED_CONTENT_CAP:] for k, v in used.items()}
        with open(USED_CONTENT_PATH, "w", encoding="utf-8") as fh:
            json.dump(capped, fh, indent=2)
    except Exception as e:
        logger.warning(f"Could not save used_content.json: {e}")


def append_revision_log(bulletin: Dict) -> None:
    """Appends today's FULL vocab/idiom/GK content (not just identifiers) to the
    revision log, used later by revision_digest.py to compile a 10-day summary."""
    try:
        log = []
        if REVISION_LOG_PATH.exists():
            with open(REVISION_LOG_PATH, "r", encoding="utf-8") as fh:
                log = json.load(fh)

        log.append({
            "date": bulletin.get("date", ""),
            "vocab_words": bulletin.get("vocab_words", []),
            "idioms_of_the_day": bulletin.get("idioms_of_the_day", []),
            "static_gk_boosters": bulletin.get("static_gk_boosters", []),
        })
        log = log[-REVISION_LOG_CAP:]

        REVISION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(REVISION_LOG_PATH, "w", encoding="utf-8") as fh:
            json.dump(log, fh, indent=2)
    except Exception as e:
        logger.warning(f"Could not update revision_log.json: {e}")


def _record_used(used: Dict[str, List[str]], bulletin: Dict) -> Dict[str, List[str]]:
    """Appends today's vocab/idiom/GK identifiers onto the rolling history."""
    for v in bulletin.get("vocab_words", []) or []:
        word = (v.get("word") or "").strip().upper()
        if word and word not in used["vocab"]:
            used["vocab"].append(word)
    for i in bulletin.get("idioms_of_the_day", []) or []:
        idiom = (i.get("idiom") or "").strip()
        if idiom and idiom not in used["idiom"]:
            used["idiom"].append(idiom)
    for b in bulletin.get("static_gk_boosters", []) or []:
        title = (b.get("title") or "").strip()
        if title and title not in used["gk_booster"]:
            used["gk_booster"].append(title)
    return used

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


def build_gemini_prompt(
    articles: List[Dict],
    exam_type: str,
    today_str: str,
    recent_vocab: Optional[List[str]] = None,
    recent_idioms: Optional[List[str]] = None,
    recent_gk_topics: Optional[List[str]] = None,
) -> str:
    """Builds a structured prompt for Gemini to process current affairs."""
    exam_guide = EXAM_INSTRUCTIONS.get(exam_type, EXAM_INSTRUCTIONS["ALL"])

    avoid_section = ""
    if recent_vocab or recent_idioms or recent_gk_topics:
        avoid_section = "\nIMPORTANT - AVOID REPETITION FROM RECENT DAYS:\n"
        if recent_vocab:
            avoid_section += f"- Do NOT reuse these recently used vocab words: {', '.join(recent_vocab[-30:])}\n"
        if recent_idioms:
            avoid_section += f"- Do NOT reuse these recently used idioms: {', '.join(recent_idioms[-30:])}\n"
        if recent_gk_topics:
            avoid_section += f"- Do NOT reuse these recently covered GK booster topics: {', '.join(recent_gk_topics[-30:])}\n"
        avoid_section += "Choose genuinely different words/idioms/topics from the ones listed above.\n"

    # Prepare top 18 candidate news items for context (concise to prevent context/token overflow)
    news_corpus = []
    for i, a in enumerate(articles[:18], 1):
        news_corpus.append(
            f"[{i}] Category: {a.get('category')}\n"
            f"Title: {a.get('title')}\n"
            f"Summary: {a.get('summary')[:220]}\n"
            f"Source URL: {a.get('link')}"
        )
    news_text = "\n\n".join(news_corpus)

    return f"""You are an expert faculty and current affairs editor specializing in Indian competitive exams (UPSC, Banking, SSC, RRB).
Today's Date: {today_str}
Target Exam Profile: {exam_type}
Guideline for this Exam: {exam_guide}

Here are today's verified news articles:
{news_text}
{avoid_section}
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
  "vocab_words": [
    {{
      "word": "EXAM_VOCAB_WORD (high-frequency editorial word relevant for SSC & Bank English, must be different from commonly overused examples like 'exigency')",
      "part_of_speech": "Adjective/Noun/Verb",
      "meaning": "Clear, concise definition",
      "synonyms": ["synonym 1", "synonym 2", "synonym 3"],
      "antonyms": ["antonym 1", "antonym 2"],
      "example_sentence": "An exam-grade sentence demonstrating its usage."
    }}
  ],
  "idioms_of_the_day": [
    {{
      "idiom": "A commonly tested English idiom or phrase, different each day",
      "meaning": "Clear, concise meaning of the idiom",
      "example_sentence": "An exam-grade sentence using the idiom naturally."
    }}
  ],
  "static_gk_boosters": [
    {{
      "title": "Topic in Today's News (e.g. Kaziranga National Park / Monetary Policy Committee / Election Commission / Ramsar Sites)",
      "bullets": [
        "Key constitutional / legal basis or founding year",
        "Geographical location, associated river, or institutional headquarters",
        "Important exam trivia frequently asked in SSC/Banking/UPSC"
      ]
    }}
  ],
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

Provide 3 to 4 categories with 2 high-yield items each.
Provide exactly 5 high-yield vocab_words (rotate topics daily, avoid repeating recent words, no duplicates within the same day).
Provide exactly 5 idioms_of_the_day (rotate idioms daily, avoid repeating recent idioms, no duplicates within the same day).
Provide exactly 5 static_gk_boosters, each on a different topic drawn from today's news where possible.
Provide exactly 5 high-quality exam MCQs in daily_quiz.
Respond ONLY with the valid JSON object. Do not include markdown preamble, commentary, or conversational text.
"""


def _extract_json(text: str) -> Optional[Dict]:
    """Robustly parses JSON from LLM responses, stripping reasoning blocks, markdown fences, and repairing truncated JSON."""
    if not text:
        return None
    cleaned = text.strip()

    # 1. Strip reasoning blocks emitted by thinking/reasoning models (e.g. gpt-oss, qwen, nemotron)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()
    cleaned = re.sub(r"\[THINK\].*?\[/THINK\]", "", cleaned, flags=re.DOTALL).strip()

    # 2. Extract from markdown code fences if present (```json ... ``` or ``` ... ```)
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if code_block:
        candidate = code_block.group(1).strip()
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 3. Direct JSON parse
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 4. Outermost JSON brackets
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # 5. Repair truncated JSON if the model stopped mid-generation
    if start != -1:
        try:
            cand = cleaned[start:]
            stack = []
            in_str = False
            esc = False
            for ch in cand:
                if esc:
                    esc = False
                    continue
                if ch == '\\':
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch == '{':
                        stack.append('}')
                    elif ch == '[':
                        stack.append(']')
                    elif ch in '}]':
                        if stack and stack[-1] == ch:
                            stack.pop()
            if in_str:
                cand += '"'
            cand = re.sub(r",\s*$", "", cand)
            cand += "".join(reversed(stack))
            parsed = json.loads(cand)
            logger.info("Successfully repaired and parsed truncated JSON response.")
            return parsed
        except Exception as e:
            logger.debug(f"JSON truncation repair failed: {e}")

    logger.warning(f"Failed to parse JSON. Raw snippet: {cleaned[:250]}...")
    return None


def _normalize_bulletin(data: Dict, date_str: str, exam_type: str, source: str) -> Dict:
    """Ensures consistent schema and fields across all AI providers."""
    data.setdefault("date", date_str)
    data.setdefault("exam_type", exam_type)
    data.setdefault("headline_summary", "Today's daily exam current affairs briefing.")
    data.setdefault("categories", [])
    data.setdefault("daily_quiz", [])
    data["content_source"] = source

    if not isinstance(data.get("vocab_words"), list):
        if isinstance(data.get("vocab_word"), dict):
            data["vocab_words"] = [data["vocab_word"]]
        else:
            data["vocab_words"] = []

    if not isinstance(data.get("idioms_of_the_day"), list):
        if isinstance(data.get("idiom_of_the_day"), dict):
            data["idioms_of_the_day"] = [data["idiom_of_the_day"]]
        else:
            data["idioms_of_the_day"] = []

    if not isinstance(data.get("static_gk_boosters"), list):
        if isinstance(data.get("static_gk_booster"), dict):
            data["static_gk_boosters"] = [data["static_gk_booster"]]
        else:
            data["static_gk_boosters"] = []

    return data


def curate_news_with_gemini(
    articles: List[Dict],
    exam_type: str,
    api_key: str,
    used_content: Optional[Dict[str, List[str]]] = None,
    model_override: Optional[str] = None,
) -> Optional[Dict]:
    """Uses Google GenAI SDK to curate and structure current affairs."""
    used_content = used_content or {"vocab": [], "idiom": [], "gk_booster": []}
    model = model_override or GEMINI_MODEL
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        today_str = datetime.date.today().strftime("%d %B %Y")
        prompt = build_gemini_prompt(
            articles, exam_type, today_str,
            recent_vocab=used_content.get("vocab", []),
            recent_idioms=used_content.get("idiom", []),
            recent_gk_topics=used_content.get("gk_booster", []),
        )

        logger.info(f"Calling Gemini ({model}) for {exam_type} curation...")
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        bulletin_data = _extract_json(response.text)
        if not bulletin_data:
            logger.error("Failed to parse JSON from Gemini response.")
            return None

        bulletin_data = _normalize_bulletin(bulletin_data, today_str, exam_type, "gemini")
        logger.info(f"Successfully generated Gemini bulletin with {len(bulletin_data.get('categories', []))} categories and {len(bulletin_data.get('daily_quiz', []))} MCQs.")
        return bulletin_data

    except Exception as e:
        logger.error(f"Gemini ({model}) curation failed: {type(e).__name__}: {e}")
        return None


# ---------------------------------------------------------------------------
# Rotating fallback content banks (used only if Gemini is unavailable/fails).
# Rotated by day-of-year so repeated fallback days still show fresh content,
# instead of the same word/idiom/booster appearing every time.
# ---------------------------------------------------------------------------

VOCAB_BANK = [
    {
        "word": "EXIGENCY", "part_of_speech": "Noun",
        "meaning": "An urgent need or demand; an emergency situation requiring immediate action.",
        "synonyms": ["necessity", "urgency", "crisis", "predicament"],
        "antonyms": ["unimportance", "ease", "calm"],
        "example_sentence": "The economic exigency compelled the Finance Ministry to introduce targeted fiscal reforms.",
    },
    {
        "word": "ACQUIESCE", "part_of_speech": "Verb",
        "meaning": "To accept or agree to something without protest, often reluctantly.",
        "synonyms": ["comply", "consent", "yield", "concur"],
        "antonyms": ["object", "resist", "dissent"],
        "example_sentence": "Several member states reluctantly acquiesced to the revised trade agreement.",
    },
    {
        "word": "CATALYST", "part_of_speech": "Noun",
        "meaning": "A person or event that quickly causes significant change or action.",
        "synonyms": ["trigger", "spur", "impetus", "stimulus"],
        "antonyms": ["hindrance", "deterrent"],
        "example_sentence": "The new policy acted as a catalyst for foreign investment in the manufacturing sector.",
    },
    {
        "word": "PRAGMATIC", "part_of_speech": "Adjective",
        "meaning": "Dealing with problems in a sensible, practical way rather than through theory.",
        "synonyms": ["practical", "realistic", "sensible"],
        "antonyms": ["idealistic", "impractical"],
        "example_sentence": "Economists praised the government's pragmatic approach to managing inflation.",
    },
    {
        "word": "CONSOLIDATE", "part_of_speech": "Verb",
        "meaning": "To combine or strengthen into a more effective or coherent whole.",
        "synonyms": ["strengthen", "unify", "merge", "solidify"],
        "antonyms": ["weaken", "fragment", "divide"],
        "example_sentence": "The merger aims to consolidate the bank's position in the retail lending market.",
    },
    {
        "word": "DIVERGENT", "part_of_speech": "Adjective",
        "meaning": "Tending to develop differently or move in different directions.",
        "synonyms": ["differing", "varying", "conflicting"],
        "antonyms": ["convergent", "similar", "uniform"],
        "example_sentence": "The committee members held divergent views on the proposed constitutional amendment.",
    },
    {
        "word": "MANDATE", "part_of_speech": "Noun",
        "meaning": "An official order or authorization to act in a particular way on a public issue.",
        "synonyms": ["authorization", "directive", "sanction"],
        "antonyms": ["prohibition", "refusal"],
        "example_sentence": "The commission was given a fresh mandate to review electoral reforms.",
    },
    {
        "word": "AMELIORATE", "part_of_speech": "Verb",
        "meaning": "To make a bad or unsatisfactory situation better.",
        "synonyms": ["improve", "enhance", "alleviate"],
        "antonyms": ["worsen", "aggravate"],
        "example_sentence": "The new subsidy scheme is expected to ameliorate rural farmers' financial distress.",
    },
    {
        "word": "SCRUTINIZE", "part_of_speech": "Verb",
        "meaning": "To examine or inspect something closely and thoroughly.",
        "synonyms": ["examine", "inspect", "analyze"],
        "antonyms": ["overlook", "ignore"],
        "example_sentence": "The parliamentary panel scrutinized the budget allocations line by line.",
    },
    {
        "word": "UNPRECEDENTED", "part_of_speech": "Adjective",
        "meaning": "Never done or known before.",
        "synonyms": ["unparalleled", "unmatched", "novel"],
        "antonyms": ["usual", "common"],
        "example_sentence": "The heatwave triggered unprecedented demand for power across northern states.",
    },
]

IDIOM_BANK = [
    {
        "idiom": "A drop in the ocean",
        "meaning": "A very small amount compared to what is needed; negligible in comparison.",
        "example_sentence": "The relief fund, though welcome, was a drop in the ocean compared to the flood damage.",
    },
    {
        "idiom": "Back to the drawing board",
        "meaning": "To start a task or plan again because the previous attempt failed.",
        "example_sentence": "After the bill was rejected in the assembly, the committee went back to the drawing board.",
    },
    {
        "idiom": "Cut corners",
        "meaning": "To do something in the easiest or cheapest way, often sacrificing quality.",
        "example_sentence": "Auditors found the contractor had cut corners on the highway's safety standards.",
    },
    {
        "idiom": "On the same page",
        "meaning": "In agreement; having the same understanding of a situation.",
        "example_sentence": "All coalition partners were finally on the same page regarding the disaster relief bill.",
    },
    {
        "idiom": "A blessing in disguise",
        "meaning": "Something that seems bad or unlucky at first but results in something good.",
        "example_sentence": "The delayed monsoon turned out to be a blessing in disguise for the reservoir levels.",
    },
    {
        "idiom": "Bite the bullet",
        "meaning": "To face a difficult or unpleasant situation with courage.",
        "example_sentence": "The finance ministry finally bit the bullet and raised fuel taxes to curb the deficit.",
    },
    {
        "idiom": "Turn the tide",
        "meaning": "To reverse a trend or change the course of events significantly.",
        "example_sentence": "The vaccination drive helped turn the tide against the outbreak in rural districts.",
    },
    {
        "idiom": "Under the weather",
        "meaning": "Feeling slightly ill.",
        "example_sentence": "Though feeling under the weather, the minister still attended the parliamentary session.",
    },
    {
        "idiom": "Get the ball rolling",
        "meaning": "To start something or set a process in motion.",
        "example_sentence": "The ministry got the ball rolling on the new skill development scheme this week.",
    },
    {
        "idiom": "Read between the lines",
        "meaning": "To understand a hidden or implied meaning beyond what is directly stated.",
        "example_sentence": "Analysts had to read between the lines of the RBI governor's cautious statement.",
    },
]

GK_BOOSTER_BANK = [
    {
        "title": "Monetary Policy Committee (MPC) & RBI Basics",
        "bullets": [
            "Constituted under Section 45ZB of the Reserve Bank of India Act, 1934.",
            "Consists of 6 members: 3 from RBI (including RBI Governor as ex-officio Chairperson) and 3 external members appointed by the Government.",
            "Each member has one vote; the Governor has a casting vote in case of a tie.",
        ],
    },
    {
        "title": "Election Commission of India (ECI)",
        "bullets": [
            "Established on 25 January 1950 under Article 324 of the Constitution.",
            "A permanent constitutional body responsible for administering elections at the Union and State level.",
            "Headed by the Chief Election Commissioner, headquartered in New Delhi.",
        ],
    },
    {
        "title": "Ramsar Sites & Wetlands in India",
        "bullets": [
            "Ramsar Convention (1971) is an international treaty for the conservation of wetlands.",
            "India has one of the largest networks of Ramsar sites in Asia, spread across multiple states.",
            "Wetlands act as natural water purifiers and are critical for migratory bird habitats.",
        ],
    },
    {
        "title": "ISRO & Space Missions Basics",
        "bullets": [
            "Indian Space Research Organisation (ISRO) was established in 1969, headquartered in Bengaluru.",
            "Operates under the Department of Space, directly overseen by the Prime Minister's Office.",
            "Known for cost-effective missions including lunar, solar, and Mars exploration programs.",
        ],
    },
    {
        "title": "Goods and Services Tax (GST) Council",
        "bullets": [
            "Constituted under Article 279A of the Constitution via the 101st Constitutional Amendment Act, 2016.",
            "Chaired by the Union Finance Minister, with state finance ministers as members.",
            "Responsible for recommending GST rates, exemptions, and dispute resolution mechanisms.",
        ],
    },
    {
        "title": "National Green Tribunal (NGT)",
        "bullets": [
            "Established in 2010 under the National Green Tribunal Act for effective environmental dispute resolution.",
            "Has original jurisdiction over substantial questions relating to the environment.",
            "Principal bench is located in New Delhi, with regional benches across India.",
        ],
    },
    {
        "title": "Finance Commission of India",
        "bullets": [
            "Constituted under Article 280 of the Constitution, typically every five years.",
            "Recommends the distribution of tax revenues between the Union and the States.",
            "Headed by a Chairman appointed by the President of India.",
        ],
    },
    {
        "title": "National Human Rights Commission (NHRC)",
        "bullets": [
            "Established under the Protection of Human Rights Act, 1993.",
            "A statutory (not constitutional) body headquartered in New Delhi.",
            "Typically headed by a retired Chief Justice of India.",
        ],
    },
]


def _rotating_group(
    bank: List[Dict],
    key_field: str,
    avoid: Optional[List[str]] = None,
    n: int = 5,
) -> List[Dict]:
    """Rotates a WINDOW of n items through a content bank based on day-of-year,
    preferring items whose key_field value is NOT in the avoid list (recently used).
    Falls back to the full bank if avoiding everything would leave too few items
    (i.e. the bank is smaller than the recent-history window)."""
    avoid_set = set(a.strip().upper() for a in (avoid or []))
    candidates = [item for item in bank if str(item.get(key_field, "")).strip().upper() not in avoid_set]
    if len(candidates) < n:
        candidates = bank  # bank exhausted by history; best effort, accept a repeat

    day_of_year = datetime.date.today().timetuple().tm_yday
    size = len(candidates)
    start = day_of_year % size
    return [candidates[(start + i) % size] for i in range(min(n, size))]


def curate_news_heuristic(
    articles: List[Dict],
    exam_type: str,
    used_content: Optional[Dict[str, List[str]]] = None,
) -> Dict:
    """
    Intelligent rule-based fallback when Gemini API key is not supplied or offline.
    Categorizes news based on domain keywords and generates practice MCQs.
    """
    used_content = used_content or {"vocab": [], "idiom": [], "gk_booster": []}
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

    # Rotating fallback Vocab / Idiom / GK Booster groups, skipping recently used ones
    vocab_group = _rotating_group(VOCAB_BANK, "word", used_content.get("vocab", []), 5)
    idiom_group = _rotating_group(IDIOM_BANK, "idiom", used_content.get("idiom", []), 5)
    booster_group = _rotating_group(GK_BOOSTER_BANK, "title", used_content.get("gk_booster", []), 5)

    return {
        "date": today_str,
        "exam_type": exam_type,
        "headline_summary": f"Daily Current Affairs Digest curated specifically for {exam_type} aspirants covering key national, economic, and scientific developments.",
        "categories": bulletin_categories,
        "vocab_words": vocab_group,
        "idioms_of_the_day": idiom_group,
        "static_gk_boosters": booster_group,
        "daily_quiz": quiz,
        "content_source": "fallback"
    }


def curate_daily_bulletin(articles: List[Dict], exam_type: str = TARGET_EXAM, api_key: str = GEMINI_API_KEY) -> Dict:
    """
    Main curation entry point:
      - Tries Gemini up to 3 times (with backoff across active 3.x models)
      - If Gemini fails all 3 attempts, falls back gracefully to Heuristic engine
    Tracks recently used vocab/idioms/GK topics across runs so content doesn't repeat.
    """
    import time
    used_content = load_used_content()
    result = None

    # --- Gemini (3 attempts with model diversity and backoff) ---
    if api_key:
        deprecated = {
            "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.5-pro",
            "gemini-2.0-flash", "gemini-2.0-flash-exp",
            "gemini-1.5-flash", "gemini-1.5-pro"
        }
        candidate_models = [GEMINI_MODEL, "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
        seen = set()
        gemini_models = []
        for m in candidate_models:
            if m and m not in deprecated and m not in seen:
                seen.add(m)
                gemini_models.append(m)
        if not gemini_models:
            gemini_models = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.5-flash"]

        for attempt in range(1, 4):
            model_to_use = gemini_models[(attempt - 1) % len(gemini_models)]
            logger.info(f"🔄 Gemini attempt {attempt}/3 using {model_to_use}...")
            result = curate_news_with_gemini(articles, exam_type, api_key, used_content, model_override=model_to_use)
            if result:
                logger.info(f"✅ Gemini succeeded on attempt {attempt} using {model_to_use}.")
                break
            if attempt < 3:
                wait_time = attempt * 5
                logger.info(f"⏳ Waiting {wait_time}s before next Gemini retry...")
                time.sleep(wait_time)

        if not result:
            logger.warning("❌ Gemini failed all 3 attempts. Falling back to heuristic engine.")

    # --- Fallback: Heuristic Engine ---
    if not result:
        logger.info("📋 Using heuristic engine fallback. Vocab & GK will rotate daily.")
        result = curate_news_heuristic(articles, exam_type, used_content)

    used_content = _record_used(used_content, result)
    save_used_content(used_content)
    append_revision_log(result)

    return result

