"""Thin wrapper around Nebius Token Factory (OpenAI-compatible API)."""
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from . import config

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        if not config.TF_API_KEY:
            raise RuntimeError("NEBIUS_API_KEY is not set (see .env.example)")
        _client = OpenAI(base_url=config.TF_BASE_URL, api_key=config.TF_API_KEY)
    return _client


def chat(prompt: str, *, system: str = "", model: str | None = None,
         temperature: float = 0.0, max_tokens: int = 1500) -> str:
    messages = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}]
    resp = client().chat.completions.create(
        model=model or config.MODEL_SMART, messages=messages,
        temperature=temperature, max_tokens=max_tokens)
    return resp.choices[0].message.content or ""


def chat_json(prompt: str, **kw) -> Any:
    """Ask for JSON and parse it robustly (strips ```json fences and <think> blocks)."""
    text = chat(prompt + "\n\nReturn ONLY valid JSON, no prose.", **kw)
    return parse_json(text)


def parse_json(text: str) -> Any:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if m:
        text = m.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=0)
    return json.loads(text[start:])
