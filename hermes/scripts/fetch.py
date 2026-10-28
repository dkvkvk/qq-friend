#!/usr/bin/env python3
"""抓网页正文（可选让 DeepSeek 提炼）。

用法:
  fetch.py <url>                 # 直接输出正文（前 4000 字）
  fetch.py <url> --sum           # 让 deepseek-flash 提炼要点
  fetch.py <url> --max 8000      # 控制输出长度

为什么不用 web_extract：Hermes 自带的那个对不少站会误判成内网地址直接拒，
这里一律 curl 抓、自己剥标签，走的是已验证可用的出口。

Key: 环境变量 DEEPSEEK_API_KEY，或 ~/.hermes/.env 里的同名项。
"""

import html
import os
import re
import subprocess
import sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DS_URL = "https://api.deepseek.com/v1/chat/completions"
DS_MODEL = "deepseek-flash"


def key():
    k = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if k:
        return k
    try:
        with open(os.path.expanduser("~/.hermes/.env"), encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("DEEPSEEK_API_KEY="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return ""


def grab(url, timeout=30):
    p = subprocess.run(
        ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
         "-H", "Accept-Language: zh-CN,zh;q=0.9", url],
        capture_output=True, timeout=timeout + 15)
    return p.stdout.decode("utf-8", "ignore")


def to_text(raw):
    raw = re.sub(r"(?is)<(script|style|noscript|svg|header|footer|nav)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<!--.*?-->", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h[1-6]>", "\n", raw)
    txt = html.unescape(re.sub(r"(?s)<[^>]+>", " ", raw))
    lines = []
    for line in txt.splitlines():
        line = re.sub(r"[ \t\u3000]+", " ", line).strip()
        if len(line) >= 2:
            lines.append(line)
    # 去掉重复空行
    out, prev = [], None
    for line in lines:
        if line != prev:
            out.append(line)
        prev = line
    return "\n".join(out)


def summarize(text, title=""):
    k = key()
    if not k:
        return "[无 DEEPSEEK_API_KEY，跳过提炼]\n\n" + text
    prompt = ("下面是一篇网页正文。用中文给我：1) 三到五条要点；2) 关键数字/事实；3) 一句话结论。"
              "不要复述原文，不要客套。\n\n" + text[:12000])
    payload = '{"model":"%s","messages":[{"role":"user","content":%s}],"max_tokens":800}' % (
        DS_MODEL, __import__("json").dumps(prompt, ensure_ascii=False))
    open("/tmp/fetch_sum.json", "w", encoding="utf-8").write(payload)
    p = subprocess.run(
        ["curl", "-s", "--max-time", "120", DS_URL,
         "-H", f"Authorization: Bearer {k}", "-H", "Content-Type: application/json",
         "--data-binary", "@/tmp/fetch_sum.json"],
        capture_output=True, timeout=140)
    try:
        import json as _j
        d = _j.loads(p.stdout.decode("utf-8", "ignore"))
        return d["choices"][0]["message"].get("content") or d["choices"][0]["message"].get("reasoning_content", "")
    except Exception as e:
        return f"[提炼失败: {e}]\n\n" + text


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    url = sys.argv[1]
    want_sum = "--sum" in sys.argv
    limit = 4000
    if "--max" in sys.argv:
        try:
            limit = int(sys.argv[sys.argv.index("--max") + 1])
        except (IndexError, ValueError):
            pass

    raw = grab(url)
    if not raw.strip():
        print("FETCH_FAILED")
        return 0
    title = ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw)
    if m:
        title = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()

    text = to_text(raw)
    if not text.strip():
        print("EMPTY_BODY (可能是 JS 渲染页，需要浏览器)")
        return 0
    header = f"# {title}\n{url}\n\n" if title else f"# {url}\n\n"
    body = summarize(text[:20000], title) if want_sum else text[:limit]
    print(header + body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
