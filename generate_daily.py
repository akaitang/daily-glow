#!/usr/bin/env python3
"""Generate one sourced Daily Glow edition via the OpenAI Responses API."""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
TODAY_FILE = CONTENT / "today.json"
ARCHIVE_FILE = CONTENT / "archive.json"
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
ALLOWED_DOMAINS = [
    "nhs.uk", "apa.org", "cdc.gov", "who.int", "nih.gov", "pubmed.ncbi.nlm.nih.gov",
    "plato.stanford.edu", "iep.utm.edu", "britannica.com", "nasa.gov", "noaa.gov",
    "si.edu", "kew.org", "nationalzoo.si.edu", "smithsonianmag.com", "un.org",
    "ourworldindata.org", "nature.com", "science.org", "hhs.gov", "nps.gov"
]

CARD = {
    "type": "object",
    "properties": {
        "title": {"type": "string"}, "body": {"type": "string"},
        "practice": {"type": "string"}, "source": {"type": "string"}, "url": {"type": "string"}
    },
    "required": ["title", "body", "practice", "source", "url"],
    "additionalProperties": False
}
FACT = {
    "type": "object",
    "properties": {
        "title": {"type": "string"}, "big": {"type": "string"}, "body": {"type": "string"},
        "source": {"type": "string"}, "url": {"type": "string"}, "symbol": {"type": "string"}
    },
    "required": ["title", "big", "body", "source", "url", "symbol"],
    "additionalProperties": False
}
SCHEMA = {
    "type": "object",
    "properties": {
        "date": {"type": "string"}, "theme": {"type": "string"},
        "quote": CARD, "psychology": CARD, "science": CARD, "philosophy": CARD, "action": CARD,
        "worldFacts": {"type": "array", "items": FACT}
    },
    "required": ["date", "theme", "quote", "psychology", "science", "philosophy", "action", "worldFacts"],
    "additionalProperties": False
}


def normalize_url(value):
    p = urlparse(value.strip())
    if p.scheme != "https" or not p.netloc:
        return ""
    return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), "", "", ""))


def extract_text(response):
    pieces = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text" and part.get("text"):
                    pieces.append(part["text"])
    if not pieces:
        raise RuntimeError("API response did not contain output_text")
    return "\n".join(pieces)


def extract_search_urls(response):
    urls = set()
    for item in response.get("output", []):
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            for source in action.get("sources", []) or []:
                url = normalize_url(source.get("url", ""))
                if url:
                    urls.add(url)
    return urls


def main():
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("OPENAI_API_KEY is missing; no new content generated.", file=sys.stderr)
        sys.exit(2)

    today = datetime.now(ZoneInfo("Asia/Taipei")).date().isoformat()
    try:
        archive = json.loads(ARCHIVE_FILE.read_text(encoding="utf-8")) if ARCHIVE_FILE.exists() else []
        if not isinstance(archive, list):
            archive = []
    except Exception:
        archive = []

    recent = archive[-14:]
    avoid = []
    for item in recent:
        avoid.extend(item.get("titles", []))
        avoid.extend(item.get("world_titles", []))
        if item.get("theme"):
            avoid.append(item["theme"])
    avoid_text = "\n".join(f"- {x}" for x in avoid[-100:]) or "（尚無歷史內容）"

    instructions = (
        "你是台灣繁體中文的每日生活知識編輯。請產出可供個人使用的每日微光內容，語氣溫柔、具體、不灌雞湯、不責備讀者。"
        "心理內容是一般自助教育，不做診斷、不承諾治療效果、不把推測包裝成科學定論。不得編造名人名言；quote 必須是原創短句，不可冒稱出自名人。"
        "心理學、科學、哲學與世界知識都必須使用網路搜尋查到的可信來源，網址要是實際搜尋來源，優先官方機構、學術百科或可靠科普機構。"
        "所有文字使用台灣繁體中文。請嚴格輸出符合指定 JSON Schema 的 JSON，不要輸出 Markdown。"
    )
    prompt = f"""請為日期 {today} 產生全新的一天內容。

內容要求：
1. theme：一個具體主題，聚焦減少焦慮、反覆內耗、情緒理解、界線、習慣或生活好奇心。
2. quote：一則原創佳句，約 15–35 個中文字，body 解釋其意義，practice 給一句可實行的小提醒；source/url 留空字串。
3. psychology：一個心理學／認知行為／情緒調節的實用概念，避免醫療診斷，practice 要具體；source/url 必須是本次網路搜尋可查到的可靠來源。
4. science：一個生活科學常識，避免誇大因果；source/url 必須是本次網路搜尋可查到的可靠來源。
5. philosophy：一個哲學觀念或思考方法，清楚區分古典思想與現代解讀；source/url 必須是本次網路搜尋可查到的可靠來源。
6. action：一個 1–5 分鐘能完成的小練習，不能要求花錢或提供私人資料；source/url 留空字串。
7. worldFacts：恰好兩則不同的世界之最／自然／地理／宇宙冷知識。要寫清楚衡量標準或必要的限定，避免「世界第一」定義不清；source/url 必須是本次網路搜尋可查到的可靠來源。symbol 使用一個合適 emoji。

請先搜尋資料，再寫內容。不得把未查證的網址寫入 source/url。內容應避免與以下最近主題／標題重複，請換角度與例子：
{avoid_text}

輸出 date 必須是 {today}。"""

    payload = {
        "model": MODEL,
        "instructions": instructions,
        "input": prompt,
        "tools": [{
            "type": "web_search",
            "filters": {"allowed_domains": ALLOWED_DOMAINS},
            "search_context_size": "medium"
        }],
        "include": ["web_search_call.action.sources"],
        "text": {"format": {
            "type": "json_schema", "name": "daily_glow_content", "strict": True, "schema": SCHEMA
        }}
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as res:
            response = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        details = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API returned HTTP {e.code}: {details[:1200]}") from e

    if response.get("status") not in (None, "completed"):
        raise RuntimeError(f"OpenAI response status: {response.get('status')}")
    data = json.loads(extract_text(response))
    search_urls = extract_search_urls(response)
    if not search_urls:
        raise RuntimeError("No web-search source metadata returned; refusing to publish unsourced content.")
    if data.get("date") != today:
        raise RuntimeError(f"Generated date mismatch: expected {today}, got {data.get('date')}")
    if not isinstance(data.get("theme"), str) or not data["theme"].strip():
        raise RuntimeError("Missing daily theme")

    for key in ["quote", "psychology", "science", "philosophy", "action"]:
        card = data.get(key, {})
        for field in ["title", "body", "practice"]:
            if not isinstance(card.get(field), str) or not card[field].strip():
                raise RuntimeError(f"Missing required content: {key}.{field}")
    if len(data.get("worldFacts", [])) != 2:
        raise RuntimeError("worldFacts must contain exactly two items")

    cited = []
    for key in ["psychology", "science", "philosophy"]:
        cited.append((key, data[key].get("source", ""), data[key].get("url", "")))
    for i, fact in enumerate(data["worldFacts"], 1):
        cited.append((f"worldFacts[{i}]", fact.get("source", ""), fact.get("url", "")))
    for label, source, url in cited:
        normalized = normalize_url(url)
        if not source.strip() or not normalized:
            raise RuntimeError(f"Missing source or HTTPS URL for {label}")
        if normalized not in search_urls:
            raise RuntimeError(f"Source URL for {label} was not found in returned web-search sources: {url}")

    recent_titles = {str(t).strip().casefold() for t in avoid}
    all_new_titles = [data[k]["title"] for k in ["quote", "psychology", "science", "philosophy", "action"]]
    all_new_titles += [f["title"] for f in data["worldFacts"]]
    duplicates = [t for t in all_new_titles if t.strip().casefold() in recent_titles]
    if duplicates:
        raise RuntimeError("Duplicate recent titles detected; refusing to publish: " + ", ".join(duplicates))

    CONTENT.mkdir(parents=True, exist_ok=True)
    TODAY_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archive = [item for item in archive if item.get("date") != today]
    archive.append({
        "date": today,
        "theme": data["theme"],
        "titles": all_new_titles[:5],
        "world_titles": [f["title"] for f in data["worldFacts"]]
    })
    ARCHIVE_FILE.write_text(json.dumps(archive[-30:], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated sourced Daily Glow content for {today}; verified {len(cited)} source URLs against web-search metadata.")


if __name__ == "__main__":
    main()
