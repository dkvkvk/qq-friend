#!/usr/bin/env python3
"""Read a local image through the ClinePass gateway and print what it says.

The chat model IS multimodal (OpenRouter metadata: input text+image), but the
Cline pass route silently drops image parts and Hermes' vision_analyze can't
parse this gateway's {"data": {...}} envelope, so this helper calls the models
directly: free vision models first, then the real model via OpenRouter.

Usage:  see.py <image> [question]
"""

import base64
import io
import json
import os
import subprocess
import sys

KEY = os.environ.get("CLINE_API_KEY") or "sk-REPLACE_ME"
URL = "https://api.cline.bot/api/v1/chat/completions"
MODELS = ["cline-pass/deepseek-v4.1-flash-1017"]


def encode(path, max_side=1024):
    from PIL import Image

    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


def _one_openrouter(b64, question, model="deepseek/deepseek-v4.1-flash-1017", max_tokens=500):
    """Fallback that goes through OpenRouter with a small max_tokens (the OR balance is tiny)."""
    key = ""
    try:
        with open(os.path.expanduser("~/.hermes/.env"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("OPENROUTER_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    except OSError:
        pass
    if not key:
        return "ERR: no OPENROUTER_API_KEY"
    payload = {"model": model, "messages": [{"role": "user", "content": [
        {"type": "text", "text": question},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]}], "max_tokens": max_tokens}
    tmp = "/tmp/see_or.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    proc = subprocess.run(
        ["curl", "-s", "--max-time", "120", "https://openrouter.ai/api/v1/chat/completions",
         "-H", f"Authorization: Bearer {key}", "-H", "Content-Type: application/json",
         "--data-binary", f"@{tmp}"], capture_output=True, timeout=140)
    raw = proc.stdout.decode("utf-8", errors="ignore")
    try:
        d = json.loads(raw)
    except Exception:
        return f"RAW: {raw[:200]}"
    if "error" in d:
        return f"ERR: {d['error']}"
    ch = d.get("choices") or []
    if not ch:
        return "EMPTY"
    msg = ch[0].get("message") or {}
    return msg.get("content") or msg.get("reasoning") or "EMPTY"


def ask(path, question="直接输出这张图上的所有中文文字，一行一条，不要任何分析、编号或说明。", max_tokens=1200, tries=2):
    """One model (ClinePass deepseek), short backoff retries."""
    import time

    b64 = encode(path)
    last = "ERR: no model answered"
    for attempt in range(tries):
        for model in MODELS:
            out = _one(model, b64, question, max_tokens)
            if not out.startswith(("ERR", "EMPTY", "RAW")):
                return out
            last = out
        time.sleep(3 * (attempt + 1))
    return last


def _one(model, b64, question, max_tokens):
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": question},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
        ]}],
        "max_tokens": max_tokens,
        # Force the DeepSeek route: the gateway's default (Vercel) silently
        # drops image parts and answers "empty response content".
        "provider": {"order": ["deepseek"], "allow_fallbacks": True},
    }
    tmp = "/tmp/see_payload.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    proc = subprocess.run(
        ["curl", "-s", "--max-time", "120", URL,
         "-H", f"Authorization: Bearer {KEY}",
         "-H", "Content-Type: application/json",
         "--data-binary", f"@{tmp}"],
        capture_output=True, timeout=140,
    )
    raw = proc.stdout.decode("utf-8", errors="ignore")
    try:
        data = json.loads(raw)
    except Exception:
        return f"RAW: {raw[:300]}"
    if "error" in data and "data" not in data:
        return f"ERR: {data['error']}"
    choices = (data.get("data") or data).get("choices") or []
    if not choices:
        return f"EMPTY: {raw[:200]}"
    return (choices[0].get("message") or {}).get("content") or "EMPTY"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    q = sys.argv[2] if len(sys.argv) > 2 else "这张图上的中文文字是什么？原样读出，不要解释。"
    print(ask(sys.argv[1], q))
