#!/usr/bin/env python3
"""DeepSeek 官方 Search / Fetch 工具。

- search.py "查询" [--count 8] [--content] [--sum]
- search.py --fetch <url>

Search 走 https://api.deepseek.com/v1/tools/search（自研搜索引擎，支持
site:/lang:/after:/before:/"精确短语" 等语法）；
Fetch 走 /v1/tools/fetch，返回 Markdown 正文。

计费：各 5 元/1000 次成功请求；无结果/失败不计费。
Key：环境变量 DEEPSEEK_API_KEY 或 ~/.hermes/.env。
"""

import json
import os
import subprocess
import sys

BASE = "https://api.deepseek.com"
SEARCH = f"{BASE}/v1/tools/search"
FETCH = f"{BASE}/v1/tools/fetch"
CHAT = f"{BASE}/v1/chat/completions"


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


def post(url, payload, timeout=90):
    tmp = "/tmp/ds_tool.json"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    p = subprocess.run(
        ["curl", "-s", "--max-time", str(timeout), url,
         "-H", f"Authorization: Bearer {key()}",
         "-H", "Content-Type: application/json",
         "--data-binary", f"@{tmp}"],
        capture_output=True, timeout=timeout + 20)
    raw = p.stdout.decode("utf-8", "ignore")
    try:
        return json.loads(raw), None
    except Exception:
        return None, raw[:200]


def do_search(q, count=8, need_content=False, ori=None):
    payload = {"query": q, "count": count, "need_content": need_content}
    if ori:
        payload["ori_question"] = ori
    return post(SEARCH, payload)


def do_fetch(url):
    return post(FETCH, {"url": url})


def summarize(q, results):
    ctx = []
    for r in results[:8]:
        ctx.append(f"《{r.get('title','')}》{r.get('date') or ''}\n{r.get('summary') or r.get('snippet') or ''}\n{r.get('url','')}")
    prompt = ("用户问题：" + q + "\n\n以下是搜索结果。用中文回答：先给结论，再给 3-5 条要点，"
              "关键数字写准，末尾列来源链接。不要客套，不要重复原句。\n\n" + "\n\n".join(ctx))
    return post(CHAT, {"model": "deepseek-flash",
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 1200}, timeout=120)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    if sys.argv[1] in {"--fetch", "-f"}:
        if len(sys.argv) < 3:
            print("用法: search.py --fetch <url>")
            return 2
        d, err = do_fetch(sys.argv[2])
        if d is None or "error" in (d or {}):
            print("FETCH_FAILED:", (d or {}).get("error") or err)
            return 0
        print(f"# {d.get('title') or sys.argv[2]}\n{sys.argv[2]}\n")
        print((d.get("content") or "")[:8000])
        return 0

    q = sys.argv[1]
    count = 8
    if "--count" in sys.argv:
        try:
            count = int(sys.argv[sys.argv.index("--count") + 1])
        except (IndexError, ValueError):
            pass
    need_content = "--content" in sys.argv
    want_sum = "--sum" in sys.argv

    d, err = do_search(q, count, need_content)
    if d is None or "error" in (d or {}):
        print("SEARCH_FAILED:", (d or {}).get("error") or err)
        return 0
    results = d.get("results") or []
    if not results:
        print("NO_RESULTS")
        return 0

    if want_sum:
        s, serr = summarize(q, results)
        if s and "choices" in s:
            print(s["choices"][0]["message"].get("content") or "")
        else:
            print("(摘要失败)", serr)

    print("\n## 结果")
    for r in results:
        flag = ""
        rs = r.get("rerank_score")
        if isinstance(rs, (int, float)):
            flag = " ★" if rs >= 1.5 else ""
        print(f"- {r.get('title','(无标题)')}{flag}")
        print(f"  {r.get('url','')}")
        if r.get("date"):
            print(f"  {r['date'][:10]}", end="")
        if r.get("site_name"):
            print(f" · {r['site_name']}", end="")
        print()
        if r.get("snippet"):
            print(f"  {r['snippet'][:160]}")
        if need_content and r.get("content"):
            print(f"  [正文 {len(r['content'])} 字]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
