#!/usr/bin/env python3
"""网页搜索，无 key：搜狗（中文）优先，DuckDuckGo lite 兜底。

用法: websearch.py "查询词" [条数]
输出: 标题 / URL / 摘要，条间空行。
"""

import html
import re
import subprocess
import sys
import urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def curl(url, timeout=25):
    try:
        return subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-A", UA,
             "-H", "Accept-Language: zh-CN,zh;q=0.9", url],
            capture_output=True, timeout=timeout + 15,
        ).stdout.decode("utf-8", "ignore")
    except subprocess.TimeoutExpired:
        return ""


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def sogou(q, limit):
    page = curl("https://www.sogou.com/web?query=" + urllib.parse.quote(q))
    if "vr-title" not in page:
        return []
    out = []
    for block in re.split(r'<h3 class="vr-title', page)[1:]:
        m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not m:
            continue
        href = m.group(1)
        if href.startswith("/link?"):
            href = "https://www.sogou.com" + href
        title = clean(m.group(2))
        body = clean(block[:1500])
        snip = body[len(title):][:180].strip() if title else body[:180]
        if title:
            out.append((title, href, snip))
        if len(out) >= limit:
            break
    return out


def ddg(q, limit):
    page = curl("https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(q))
    rows = re.findall(
        r"<a[^>]+href=\"([^\"]+)\"[^>]*class=['\"]result-link['\"][^>]*>(.*?)</a>", page, re.S)
    snips = re.findall(r"class=['\"]result-snippet['\"][^>]*>(.*?)</td>", page, re.S)
    out = []
    for i, (href, title) in enumerate(rows[:limit]):
        m = re.search(r"uddg=([^&]+)", href)
        url = urllib.parse.unquote(m.group(1)) if m else href
        if url.startswith("//"):
            url = "https:" + url
        snip = clean(snips[i])[:180] if i < len(snips) else ""
        out.append((clean(title), url, snip))
    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    q = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    results = sogou(q, limit) or ddg(q, limit)
    if not results:
        print("NO_RESULTS")
        return 0
    for title, url, snip in results:
        print(title)
        print(url)
        if snip:
            print(snip)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
