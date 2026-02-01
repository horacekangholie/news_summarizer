from __future__ import annotations

import argparse
import logging
import os
import webbrowser

from dotenv import load_dotenv

from news_summarizer.llm.factory import build_provider_from_env
from news_summarizer.llm.base import LLMBlockedByRegionError
from news_summarizer.llm.factory import build_provider
from news_summarizer.report import build_markdown_report, markdown_to_html, wrap_html, write_html
from news_summarizer.rss import extract_entries, fetch_google_news_top_stories
from news_summarizer.summarizer import summarize_stories




def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Summarize Google News Top Stories into a styled HTML report.")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output", type=str, default="out/index.html")
    p.add_argument("--max-chars", type=int, default=450)
    p.add_argument("--fail-fast", action="store_true")
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--rss", type=str, default=None)
    p.add_argument("--llm", type=str, default=None, help="openai or ollama")
    p.add_argument("--log-level", type=str, default="INFO")
    p.add_argument("--refresh-geoip", action="store_true", help="Ignore geoip cache and re-detect location.")
    return p

def language_instruction_from_locale(locale_lang: str) -> str:
    lang = locale_lang.lower()

    if lang.startswith("zh-tw") or lang.startswith("zh-hk") or lang.startswith("zh-mo"):
        return "Traditional Chinese (繁體中文)"
    if lang.startswith("zh-cn"):
        return "Simplified Chinese (简体中文)"
    if lang.startswith("ja"):
        return "Japanese (日本語)"
    if lang.startswith("ko"):
        return "Korean (한국어)"
    if lang.startswith("fr"):
        return "French (français)"
    if lang.startswith("de"):
        return "German (Deutsch)"

    return "English"

def main() -> None:
    load_dotenv()

    args = build_arg_parser().parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("news_summarizer")

    if args.llm:
        os.environ["LLM_PROVIDER"] = args.llm.strip().lower()
    
    llm_provider_name = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()

    from news_summarizer.localize import resolve_locale, build_google_news_rss_url

    locale = resolve_locale(force_refresh=args.refresh_geoip)
    
    if args.rss:
        rss_url = args.rss
    elif os.getenv("GOOGLE_NEWS_RSS"):
        rss_url = os.getenv("GOOGLE_NEWS_RSS")
    else:
        rss_url = build_google_news_rss_url(locale)

    logger.info("Resolved RSS URL: %s", rss_url)
    # Decide LLM output language from locale
    target_language = language_instruction_from_locale(locale.lang)
    logger.info("Target summary language: %s", target_language)

    primary_provider = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
    llm = build_provider(primary_provider)

    logger.info("Fetching RSS feed: %s", rss_url)
    feed = fetch_google_news_top_stories(rss_url)
    stories = extract_entries(feed, limit=args.limit)
    if not stories:
        raise SystemExit("No stories found. RSS may be blocked or returned empty.")

    llm_provider_name = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()
    llm = build_provider(llm_provider_name)

    try:
        items = summarize_stories(
            llm=llm,
            stories=stories,
            max_chars=args.max_chars,
            fail_fast=args.fail_fast,
            logger=logger,
            target_language=target_language,
        )

    except LLMBlockedByRegionError:
        logger.warning("OpenAI blocked in this region. Falling back to Ollama.")
        llm_provider_name = "ollama"
        llm = build_provider("ollama")

        items = summarize_stories(
            llm=llm,
            stories=stories,
            max_chars=args.max_chars,
            fail_fast=args.fail_fast,
            logger=logger,
            target_language=target_language,
        )

    except Exception:
        # last-resort: don't crash; show empty report with a visible note
        logger.exception("Summarization failed unexpectedly.")
        items = []


    markdown_report = build_markdown_report(items, rss_url=rss_url, stories=stories, llm_provider=llm_provider_name)
    body_html = markdown_to_html(markdown_report)
    full_html = wrap_html(body_html)

    abs_path = write_html(args.output, full_html)
    logger.info("Saved HTML report: %s", abs_path)

    if not args.no_open:
        webbrowser.open(f"file:///{abs_path.replace(os.sep, '/')}")


if __name__ == "__main__":
    main()
