from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List

import markdown as md

CSS = """
:root{
  --bg:#0b1220;
  --card:#0f1b33;
  --text:#e8eefc;
  --muted:#a9b7d0;
  --border:rgba(255,255,255,.08);
  --link:#7ab7ff;
  --shadow: 0 12px 30px rgba(0,0,0,.35);
}
*{ box-sizing:border-box; }
body{
  margin:0;
  font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
  background: radial-gradient(1200px 700px at 20% 0%, rgba(122,183,255,.18), transparent 60%),
              radial-gradient(900px 500px at 90% 10%, rgba(147,112,219,.16), transparent 55%),
              var(--bg);
  color:var(--text);
}
.container{ max-width: 980px; margin: 40px auto; padding: 0 18px 40px; }
.header{
  padding: 18px 18px 8px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.03);
  border-radius: 18px;
  box-shadow: var(--shadow);
}
.header h1{ margin:0; font-size: 28px; letter-spacing:.2px; }
.header .meta{
  margin-top:10px; color:var(--muted); font-size: 14px;
  display:flex; gap:12px; flex-wrap: wrap; padding-left: 18px;
}
.card{
  margin-top: 16px;
  padding: 18px 18px 14px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,.03);
  border-radius: 18px;
  box-shadow: var(--shadow);
}
.card h2{ margin:0 0 10px; font-size: 18px; }
.card p{ margin: 10px 0; line-height: 1.6; color: var(--text); }
a{ color: var(--link); text-decoration: none; }
a:hover{ text-decoration: underline; }
hr{ border: none; border-top: 1px solid var(--border); margin: 18px 0; }
code{
  background: rgba(255,255,255,.06);
  padding: 2px 6px;
  border-radius: 8px;
  border: 1px solid var(--border);
}
.footer{ margin-top: 18px; color: var(--muted); font-size: 13px; }
"""


def build_markdown_report(items: List[dict], rss_url: str, stories: List[dict], llm_provider: str) -> str:
    link_map = {s.get("title", ""): s.get("link", "") for s in stories}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines: List[str] = []
    lines.append("# Google News — Top Stories Summary")
    lines.append("")
    lines.append(f"- Generated at: **{now}**")
    lines.append("")
    lines.append(f"- RSS: {rss_url}")
    lines.append("")
    lines.append(f"- LLM Provider: `{llm_provider}`")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, item in enumerate(items, start=1):
        title = item.get("Title", "").strip()
        summary = item.get("News Summary", "").strip()
        link = link_map.get(title, "").strip()

        lines.append(f"## {i}. [{title}]({link})" if link else f"## {i}. {title}")
        lines.append("")
        lines.append(summary)
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def markdown_to_html(markdown_text: str) -> str:
    return md.markdown(markdown_text, extensions=["extra", "sane_lists"])


def wrap_html(body_html: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "  <title>News Summary</title>\n"
        f"  <style>{CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"container\">\n"
        "    <div class=\"header\"></div>\n"
        "    <div id=\"content\">\n"
        f"{body_html}\n"
        "    </div>\n"
        "    <div class=\"footer\">Tip: You can schedule this daily with Task Scheduler / cron.</div>\n"
        "  </div>\n"
        "  <script>\n"
        "    (function() {\n"
        "      const content = document.getElementById(\"content\");\n"
        "      const nodes = Array.from(content.children);\n"
        "      const newNodes = [];\n"
        "      let currentCard = null;\n"
        "      function flushCard() { if (currentCard) { newNodes.push(currentCard); currentCard = null; } }\n"
        "      for (const node of nodes) {\n"
        "        if (node.tagName === \"H1\") { document.querySelector(\".header\").appendChild(node); continue; }\n"
        "        if (node.tagName === \"UL\") { node.className = \"meta\"; document.querySelector(\".header\").appendChild(node); continue; }\n"
        "        if (node.tagName === \"HR\") continue;\n"
        "        if (node.tagName === \"H2\") {\n"
        "          flushCard();\n"
        "          currentCard = document.createElement(\"div\");\n"
        "          currentCard.className = \"card\";\n"
        "          currentCard.appendChild(node);\n"
        "          continue;\n"
        "        }\n"
        "        if (!currentCard) { currentCard = document.createElement(\"div\"); currentCard.className = \"card\"; }\n"
        "        currentCard.appendChild(node);\n"
        "      }\n"
        "      flushCard();\n"
        "      content.innerHTML = \"\";\n"
        "      for (const n of newNodes) content.appendChild(n);\n"
        "    })();\n"
        "  </script>\n"
        "</body>\n"
        "</html>\n"
    )


def write_html(output_path: str, html: str) -> str:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return str(out.resolve())
