"""Thin client for the Groq OpenAI-compatible API (chat and speech-to-text)."""
import re
import time

import requests

from . import config


def _headers():
    return {"Authorization": f"Bearer {config.GROQ_API_KEY}"}


def chat(model, messages, json_mode=True):
    """Returns the assistant text. Retries on rate limits."""
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 4096,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    for _ in range(3):
        resp = requests.post(
            f"{config.GROQ_BASE_URL}/chat/completions",
            headers=_headers(), json=body, timeout=120,
        )
        if resp.status_code == 429:
            time.sleep(min(float(resp.headers.get("retry-after", 5)), 30))
            continue
        if resp.status_code == 400 and "response_format" in body:
            del body["response_format"]
            continue
        if not resp.ok:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        text = resp.json()["choices"][0]["message"]["content"] or ""
        return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    raise RuntimeError("Groq request failed after retries")


def transcribe(filename, raw):
    """Speech to text. Returns an empty string when disabled or on failure."""
    if not (config.ALLOW_EXTERNAL_AI and config.GROQ_API_KEY):
        return ""
    for _ in range(3):
        try:
            resp = requests.post(
                f"{config.GROQ_BASE_URL}/audio/transcriptions",
                headers=_headers(),
                files={"file": (filename, raw)},
                data={"model": config.GROQ_AUDIO_MODEL, "response_format": "json"},
                timeout=180,
            )
            if resp.status_code == 429:
                time.sleep(min(float(resp.headers.get("retry-after", 5)), 30))
                continue
            resp.raise_for_status()
            return resp.json().get("text", "")
        except requests.RequestException:
            return ""
    return ""
