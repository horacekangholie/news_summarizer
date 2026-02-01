# 📰 News Summarizer (Google News + LLM)

A Python CLI tool that:
- Fetches Google News top stories (localized by country)
- Summarizes them using an LLM (OpenAI or local Ollama)
- Outputs a clean, styled HTML report
- Automatically adapts language (e.g. zh-TW in Taiwan)

---

## ✨ Features

- 🌍 Auto-localized Google News RSS (geo-IP based)
- 🧠 LLM summarization (OpenAI / Ollama switchable)
- 🌐 Multi-language summaries (Chinese, English, Japanese, etc.)
- 📄 Beautiful standalone HTML output
- 🔁 Automatic fallback when OpenAI is region-blocked

---

## Setup
```bash
python -m venv .venv
```
### Windows:
```bash
.venv\Scripts\activate
```

### macOS/Linux:
```bash
source .venv/bin/activate
```
---

## Run (OpenAI)
```bash
python src/main.py --llm openai --limit 10 --output out/index.html
python src/main.py --refresh-geoip --llm openai --limit 10 --output out/index.html
```

## Run (Ollama)
# Make sure Ollama is running:
#   ollama serve
#   ollama pull llama3.2
```bash
python src/main.py --llm ollama --limit 10 --output out/index.html
python src/main.py --refresh-geoip --llm ollama --limit 10 --output out/index.html
```