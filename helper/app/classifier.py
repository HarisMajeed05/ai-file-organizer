"""AI classification through the Groq API, with a safe rule-based fallback."""
import base64
import json
import re

from . import config
from .groq_api import chat

FALLBACK = {
    "image": "Images", "audio": "Audio", "video": "Video", "presentation": "Presentations",
    "spreadsheet": "Spreadsheets", "document": "Documents", "code": "Code", "archive": "Archives",
}

PROMPT = """You organize files. Based only on the evidence below, return one JSON object with keys:
category (one of: {cats}), subcategory (short, 1-2 words), suggested_filename (descriptive, no extension,
words separated by underscores, max 6 words), description (one sentence), confidence (number from 0 to 1).
Use low confidence if the evidence is weak. Never invent details that are not in the evidence.

Original filename: {name}
File type: {kind}
Metadata: {meta}
Extracted text:
{text}
"""


def _fallback(kind, reason):
    return {
        "category": FALLBACK.get(kind, "Other"),
        "subcategory": "",
        "suggested_filename": "",
        "description": reason,
        "confidence": 0.3,
    }


def _parse_json(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return json.loads(text[start:end + 1])


def classify(name, data):
    kind = data.get("kind", "other")
    if not config.ALLOW_EXTERNAL_AI:
        return _fallback(kind, "External AI is disabled")
    if not config.GROQ_API_KEY:
        return _fallback(kind, "No API key configured")
    images = data.get("images", [])[:3]
    if not (data.get("text") or images):
        return _fallback(kind, data.get("error") or "No readable content")

    prompt = PROMPT.format(
        cats=", ".join(config.CATEGORIES), name=name, kind=kind,
        meta=json.dumps(data.get("meta", {}), default=str),
        text=data.get("text") or "(none)",
    )
    if images:
        content = [{"type": "text", "text": prompt}]
        for mime, raw in images:
            b64 = base64.b64encode(raw).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
        model = config.GROQ_VISION_MODEL
    else:
        content = prompt
        model = config.GROQ_TEXT_MODEL

    try:
        reply = chat(model, [{"role": "user", "content": content}])
        return _parse_json(reply)
    except Exception as exc:
        return _fallback(kind, f"AI call failed: {type(exc).__name__}: {str(exc)[:300]}")
