#!/usr/bin/env python3
"""Weekly check of aigengtu.com — DeepSeek 大肥鱼表情包站.

Scans the archive listing for meme ids, downloads ones we have never seen into
~/dy-trending/whale/ (site id == filename), and prints a deterministic change
signal for the cron monitor:

    NO_CHANGE
    NEW_STICKERS <n>
    <id> <file> <bytes>
    ...

Full images live at img.aigengtu.com/meme/<id>.webp for older entries and
<id>.png for newer ones, so both are tried and the bytes are magic-checked
(a 404 answers 200 with an HTML error page, never trust the status alone).

No timestamps in stdout — this output is the change detector.
State: ~/.hermes/state/aigengtu-stickers.json
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

SITE = "https://aigengtu.com"
IMG = "https://img.aigengtu.com/meme"
PAGES = 3              # archive pages scanned each run (72 entries each)
MAX_DOWNLOAD = 8       # cap per run so a backlog never floods the library
OUT_DIR = Path(os.path.expanduser("~/dy-trending/whale"))
STATE = Path(os.path.expanduser("~/.hermes/state/aigengtu-stickers.json"))
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
EXTS = ("webp", "png")


def http_get(url, timeout=20):
    """curl: the sandbox proxy works for curl but times out for urllib."""
    try:
        proc = subprocess.run(
            ["curl", "-sL", "-A", UA, "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout + 5,
        )
    except subprocess.TimeoutExpired:
        return 1, b""
    return proc.returncode, proc.stdout


def is_image(data):
    if len(data) < 2000:
        return False
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:2] == b"\xff\xd8":  # jpeg
        return True
    return False


def load_state():
    if not STATE.exists():
        return set(), True
    try:
        data = json.loads(STATE.read_text(encoding="utf-8"))
        return set(int(i) for i in data.get("ids", [])), False
    except Exception:
        return set(), True


def save_state(ids):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"ids": sorted(ids)}), encoding="utf-8")
    tmp.replace(STATE)


def download(meme_id):
    for ext in EXTS:
        dest = OUT_DIR / f"{meme_id:03d}.{ext}"
        if dest.exists() and dest.stat().st_size > 2000:
            return dest.name, dest.stat().st_size
        rc, data = http_get(f"{IMG}/{meme_id:03d}.{ext}", timeout=30)
        if rc == 0 and is_image(data):
            dest.write_bytes(data)
            return dest.name, len(data)
    return None, 0


def main():
    if not OUT_DIR.is_dir():
        print("FETCH_FAILED output dir missing")
        return 0

    known, first_run = load_state()

    page_ids = []
    for p in range(1, PAGES + 1):
        url = f"{SITE}/archive" + (f"?p={p}" if p > 1 else "")
        rc, body = http_get(url)
        if rc != 0 or not body:
            if p == 1:
                print("FETCH_FAILED archive page1")
                return 0
            break
        page_ids.extend(int(i) for i in re.findall(rb"0_preview/meme/(\d+)\.webp", body))

    found = set(page_ids)
    if not found:
        print("FETCH_FAILED no ids parsed")
        return 0

    on_disk = {int(p.stem) for p in OUT_DIR.iterdir() if p.suffix[1:] in EXTS and p.stem.isdigit()}
    candidates = sorted(found - known - on_disk)
    if first_run:
        candidates = sorted(found)[-MAX_DOWNLOAD:]
    else:
        candidates = candidates[-MAX_DOWNLOAD:]

    downloads = []
    for meme_id in candidates:
        name, size = download(meme_id)
        if name:
            downloads.append((meme_id, name, size))

    save_state(known | on_disk | {d[0] for d in downloads})

    if not downloads:
        print("NO_CHANGE")
        return 0

    print(f"NEW_STICKERS {len(downloads)}")
    for meme_id, name, size in downloads:
        print(f"{meme_id} {name} {size}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
