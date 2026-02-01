from __future__ import annotations

import json
from typing import List

from pydantic import ValidationError

from news_summarizer.llm.base import LLMProvider
from news_summarizer.models import NewsItem
from news_summarizer.utils import extract_first_json_object, strip_html
from news_summarizer.llm.base import LLMBlockedByRegionError



def build_summary_prompt(story: dict, max_chars: int, target_language: str) -> str:
    title = story.get("title", "").strip()
    link = story.get("link", "").strip()
    source = story.get("source", "").strip()
    published = story.get("published", "").strip()
    snippet = strip_html(story.get("summary", ""))

    return f"""
    You are summarizing a news headline for a daily briefing.

    Return ONLY a JSON object with exactly these keys:
    - "Title"
    - "News Summary"

    Output language requirement:
    - Write the "News Summary" in {target_language}.

    Rules for "News Summary":
    - 2-4 sentences
    - concise, neutral tone
    - include key context and what's new
    - avoid speculation
    - max ~{max_chars} characters

    Story metadata:
    Title: {title}
    Source: {source}
    Published: {published}
    Link: {link}

    Snippet (may be incomplete):
    {snippet}
    """.strip()


def summarize_one_story(
    llm: LLMProvider,
    story: dict,
    max_chars: int,
    target_language: str,
) -> NewsItem:
    prompt = build_summary_prompt(story, max_chars=max_chars, target_language=target_language)


    text = llm.generate_text(prompt)
    if not text:
        raise RuntimeError("Empty model response.")

    try:
        json_str = extract_first_json_object(text)
        data = json.loads(json_str)
    except Exception as e:
        raise RuntimeError(f"Model did not return valid JSON. Raw output:\n{text}") from e

    try:
        return NewsItem.model_validate(data)
    except ValidationError as e:
        raise RuntimeError(f"JSON schema validation failed. Got:\n{data}") from e


def summarize_stories(
    llm: LLMProvider,
    stories: List[dict],
    max_chars: int,
    fail_fast: bool,
    logger,
    target_language: str,
) -> List[dict]:

    results: List[dict] = []

    for idx, story in enumerate(stories, start=1):
        title = story.get("title", "").strip()
        if not title:
            logger.warning("Skipping story %d: missing title", idx)
            continue

        logger.info("Summarizing %d/%d: %s", idx, len(stories), title[:80])

        try:
            item = summarize_one_story(llm, story, max_chars=max_chars, target_language=target_language)
            results.append(item.model_dump(by_alias=True))

        except LLMBlockedByRegionError:
            # Expected in some VPN regions (HK). Don't spam traceback; re-raise to trigger fallback in main.
            logger.warning("LLM blocked by region. Triggering provider fallback.")
            raise

        except Exception as e:
            # Unexpected errors: keep traceback (useful for debugging)
            logger.exception("Failed summarizing story %d", idx)
            if fail_fast:
                raise
            # else: continue


    return results
