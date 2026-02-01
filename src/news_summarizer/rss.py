from __future__ import annotations

from typing import List

import feedparser
import requests


def fetch_google_news_top_stories(rss_url: str, timeout_s: int = 20) -> feedparser.FeedParserDict:
    resp = requests.get(rss_url, timeout=timeout_s)
    resp.raise_for_status()
    return feedparser.parse(resp.text)


def extract_entries(feed: feedparser.FeedParserDict, limit: int) -> List[dict]:
    entries = []
    for e in (feed.entries or [])[:limit]:
        entries.append(
            {
                "title": getattr(e, "title", "").strip(),
                "link": getattr(e, "link", "").strip(),
                "published": getattr(e, "published", "").strip(),
                "source": getattr(getattr(e, "source", None), "title", "") if getattr(e, "source", None) else "",
                "summary": getattr(e, "summary", "").strip(),
            }
        )
    return entries
