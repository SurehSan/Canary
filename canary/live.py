"""Optional live RSS adapter (The Hacker News public feed) — CAN-REQ-003/004.

Off by default (CANARY_LIVE_SOURCES=1 enables it). Public, unauthenticated
feed only; one request per source per minimum interval; only AI-related items
are kept, and only title, link, date, and a short plain-text excerpt are stored.
"""
import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

LIVE_FEEDS = {"thehackernews": "https://feeds.feedburner.com/TheHackersNews"}
LIVE_ADAPTER = "Live RSS"
USER_AGENT = "Canary-local-demo/0.1 (local prototype; public RSS only)"
MAX_BYTES = 2_000_000
EXCERPT_CHARS = 280

AI_TERMS = re.compile(
    r"\b(ai|llms?|genai|agents?|agentic|chatbots?|copilot|mcp|prompt injection|machine learning|chatgpt|openai|"
    r"anthropic|claude|gemini|cursor|hallucinat\w*|slopsquat\w*|hallusquat\w*|model context protocol)\b",
    re.IGNORECASE)
TAG = re.compile(r"<[^>]+>")


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310 - fixed catalog URL only
        return resp.read(MAX_BYTES + 1)[:MAX_BYTES]


def _plain(text):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", text or ""))).strip()


def parse_rss(data):
    root = ET.fromstring(data)
    out = []
    for item in root.iter("item"):
        title = _plain(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if not title or not link.startswith(("https://", "http://")):
            continue
        published = None
        if item.findtext("pubDate"):
            try:
                published = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
            except (TypeError, ValueError):
                published = None
        excerpt = _plain(item.findtext("description"))
        if len(excerpt) > EXCERPT_CHARS:
            excerpt = excerpt[:EXCERPT_CHARS - 1].rsplit(" ", 1)[0] + "…"
        out.append({"title": title, "url": link, "published_at": published, "excerpt": excerpt, "source_note": None})
    return out


def is_ai_relevant(title, excerpt):
    return bool(AI_TERMS.search(f"{title} {excerpt}"))
