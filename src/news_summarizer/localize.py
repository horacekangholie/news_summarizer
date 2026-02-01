from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests


@dataclass(frozen=True)
class Locale:
    country: str  # ISO 3166-1 alpha-2, e.g. "TW"
    lang: str     # UI locale string, e.g. "zh-TW", "ja-JP", "en-US"


# --------------------------
# Auto language mapping
# --------------------------

# UI locale defaults (feel free to extend)
DEFAULT_LOCALE_BY_COUNTRY = {
    "TW": "zh-TW",
    "HK": "zh-HK",
    "MO": "zh-MO",
    "CN": "zh-CN",
    "JP": "ja-JP",
    "KR": "ko-KR",
    "SG": "en-SG",
    "MY": "en-MY",
    "TH": "th-TH",
    "VN": "vi-VN",
    "ID": "id-ID",
    "PH": "en-PH",
    "IN": "en-IN",
    "FR": "fr-FR",
    "DE": "de-DE",
    "ES": "es-ES",
    "IT": "it-IT",
    "PT": "pt-PT",
    "BR": "pt-BR",
    "RU": "ru-RU",
    "UA": "uk-UA",
}

# Google News RSS ceid language part.
# For Chinese regions, script tags often work better:
CEID_LANG_OVERRIDE = {
    "TW": "zh-Hant",
    "HK": "zh-Hant",
    "MO": "zh-Hant",
    "CN": "zh-Hans",
}

# --------------------------
# Cache (avoid rate limits)
# --------------------------

_CACHE_PATH = Path("out/geoip_cache.json")
_CACHE_TTL_SECONDS = 6 * 3600  # 6 hours


def _load_cached_country() -> Optional[str]:
    try:
        if not _CACHE_PATH.exists():
            return None
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        ts = float(data.get("ts", 0))
        country = (data.get("country") or "").strip().upper()
        if not country or len(country) != 2:
            return None
        if time.time() - ts > _CACHE_TTL_SECONDS:
            return None
        return country
    except Exception:
        return None


def _save_cached_country(country: str) -> None:
    try:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps({"ts": time.time(), "country": country}), encoding="utf-8")
    except Exception:
        pass


# --------------------------
# Geo-IP detection
# --------------------------

def _extract_country_code(data: dict) -> Optional[str]:
    # ipwho.is uses "country_code"
    for key in ("country_code", "countryCode", "country"):
        val = (data.get(key) or "").strip().upper()
        if val and len(val) == 2:
            return val
    return None


def detect_country_via_geoip(timeout_s: int = 6, force_refresh: bool = False) -> Optional[str]:
    """
    Try multiple geo-IP providers and return the first valid ISO country code.
    Uses cache to avoid rate limits.
    """
    if not force_refresh:
        cached = _load_cached_country()
        if cached:
            return cached

    providers = [
        os.getenv("GEOIP_URL", "").strip() or "https://ipwho.is/",
        "https://ipapi.co/json/",
        "https://ipinfo.io/json",
    ]

    headers = {"User-Agent": "news-summarizer/1.0"}

    for url in providers:
        try:
            r = requests.get(url, timeout=timeout_s, headers=headers)
            if r.status_code == 429:
                continue
            r.raise_for_status()
            data = r.json()
            country = _extract_country_code(data)
            if country:
                _save_cached_country(country)
                return country
        except Exception:
            continue

    return None


# --------------------------
# RSS builder
# --------------------------

def build_google_news_rss_url(locale: Locale) -> str:
    """
    Build a localized Google News RSS URL.

    Example:
      Locale(country="TW", lang="zh-TW")
      -> https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant
    """
    country = locale.country.upper()
    hl = locale.lang.strip()

    # ceid language: use script tags for Chinese regions; otherwise use base language.
    ceid_lang = CEID_LANG_OVERRIDE.get(country)
    if not ceid_lang:
        ceid_lang = hl.split("-")[0].lower()  # e.g. "ja" from "ja-JP", "en" from "en-SG"

    return f"https://news.google.com/rss?hl={hl}&gl={country}&ceid={country}:{ceid_lang}"


def resolve_locale(force_refresh: bool = False) -> Locale:
    """
    Auto language-by-country mode (A).

    Priority:
      1) NEWS_COUNTRY + NEWS_LANG overrides (for testing / VPN issues)
      2) geoip detected country -> default locale mapping
      3) default US/en-US
    """
    country_override = (os.getenv("NEWS_COUNTRY") or "").strip().upper()
    lang_override = (os.getenv("NEWS_LANG") or "").strip()

    if country_override:
        lang = lang_override or DEFAULT_LOCALE_BY_COUNTRY.get(country_override, "en-US")
        return Locale(country=country_override, lang=lang)

    detected = detect_country_via_geoip(force_refresh=force_refresh)
    if detected:
        lang = lang_override or DEFAULT_LOCALE_BY_COUNTRY.get(detected, "en-US")
        return Locale(country=detected, lang=lang)

    return Locale(country="US", lang=(lang_override or "en-US"))
