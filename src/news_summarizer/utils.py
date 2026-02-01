from __future__ import annotations

import re


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def extract_first_json_object(text: str) -> str:
    """
    Extract the first JSON object from a string.
    Handles cases like ```json { ... } ``` or extra commentary.
    """
    if not text:
        raise ValueError("Empty text")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    start = cleaned.find("{")
    if start == -1:
        raise ValueError(f"No '{{' found in model output:\n{cleaned}")

    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]

    raise ValueError(f"Unclosed JSON object in model output:\n{cleaned}")
