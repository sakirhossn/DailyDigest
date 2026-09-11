"""
RSS Fetcher for Daily Current Affairs Agent.
Retrieves, parses, sanitizes, and deduplicates news articles from verified feeds.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import RSS_FEEDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def clean_html(raw_html: str) -> str:
    """Removes HTML markup and extraneous whitespace from article text."""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    text = soup.get_text(separator=" ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fetch_single_feed(category: str, url: str, timeout: int = 10) -> List[Dict]:
    """Fetches and parses a single RSS feed."""
    articles = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
            return articles

        feed = feedparser.parse(response.content)
        for entry in feed.entries[:10]:  # Take top 10 most recent per feed
            title = clean_html(getattr(entry, "title", ""))
            summary = clean_html(getattr(entry, "summary", getattr(entry, "description", "")))
            link = getattr(entry, "link", "")
            published = getattr(entry, "published", getattr(entry, "updated", ""))

            # Filter out empty or too-short titles
            if len(title) < 15:
                continue

            articles.append({
                "category": category,
                "title": title,
                "summary": summary,
                "link": link,
                "published": published,
            })
    except Exception as e:
        logger.warning(f"Error fetching feed {url}: {e}")

    return articles


def are_titles_similar(t1: str, t2: str, threshold: float = 0.65) -> bool:
    """Simple token-overlap Jaccard similarity to prevent duplicate headlines."""
    def tokenize(text: str):
        words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
        return set(words)

    s1, s2 = tokenize(t1), tokenize(t2)
    if not s1 or not s2:
        return False
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    return (intersection / union) >= threshold


def deduplicate_articles(articles: List[Dict]) -> List[Dict]:
    """Deduplicates articles based on title similarity and exact links."""
    unique = []
    seen_links = set()

    for article in articles:
        link = article.get("link", "")
        title = article.get("title", "")

        if link and link in seen_links:
            continue

        # Check title similarity against already kept articles
        duplicate = False
        for kept in unique:
            if are_titles_similar(title, kept["title"]):
                duplicate = True
                break

        if not duplicate:
            seen_links.add(link)
            unique.append(article)

    return unique


def fetch_all_current_affairs(max_workers: int = 6) -> List[Dict]:
    """
    Fetches articles from all configured RSS feeds concurrently,
    deduplicates them, and returns a clean list of articles.
    """
    all_articles = []
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for category, urls in RSS_FEEDS.items():
            for url in urls:
                tasks.append(executor.submit(fetch_single_feed, category, url))

        for future in as_completed(tasks):
            try:
                res = future.result()
                all_articles.extend(res)
            except Exception as e:
                logger.error(f"Feed parsing task error: {e}")

    deduped = deduplicate_articles(all_articles)
    logger.info(f"Retrieved {len(all_articles)} raw news items, deduplicated to {len(deduped)} distinct stories.")
    return deduped


if __name__ == "__main__":
    print("Testing RSS fetcher...")
    news = fetch_all_current_affairs()
    for i, item in enumerate(news[:5], 1):
        print(f"\n[{i}] ({item['category']}) {item['title']}")
        print(f"    Summary: {item['summary'][:150]}...")
        print(f"    Link: {item['link']}")
