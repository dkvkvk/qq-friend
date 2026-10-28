# DeepSeek 官方 Search / Fetch

DeepSeek 自研搜索引擎，给 Agent / RAG 用的原始 JSON 接口。**不是**第三方聚合，也不走模型生成。

- 文档：<https://api-docs.deepseek.com/zh-cn/guides/search>
- Base URL：`https://api.deepseek.com`
- 鉴权：`Authorization: Bearer <DeepSeek API Key>` + `Content-Type: application/json`

---

## 两个接口

| 接口 | 路径 | 作用 |
|---|---|---|
| Search | `POST /v1/tools/search` | 按 query 搜索，返回结构化结果 |
| Fetch | `POST /v1/tools/fetch` | 抓单个网页，返回 Markdown 正文 |

两者都是**只读**请求，按次计费。

---

## Search

```bash
curl https://api.deepseek.com/v1/tools/search \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"query":"DeepSeek V4 模型 发布","count":5,"need_content":false}'
```

### 请求字段

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---|---|---|
| `query` | string | 是 | — | 1–128 字符，支持搜索语法 |
| `count` | int | 否 | 10 | 1–50 |
| `ori_question` | string | 否 | — | 触发搜索的原始问题，帮助理解意图 |
| `localization` | string | 否 | `""` | 优先本地化结果的 IP |
| `need_content` | bool | 否 | false | 是否在 `content` 返回正文（会变重、变慢） |

### 搜索语法（原样传给搜索服务，可组合）

| 操作符 | 示例 | 含义 |
|---|---|---|
| `site:` | `DeepSeek site:github.com` | 限定站点，多个用空格 + `OR` |
| `-site:` | `-site:example.com` | 排除站点 |
| `-` | `-广告` | 排除关键词 |
| `-"..."` | `-"release notes"` | 排除短语 |
| `"..."` | `"精确短语"` | 精确匹配 |
| `lang:` | `lang:zh,en` | 限定语言 |
| `after:` / `before:` | `after:2025-01-01` | 时间范围 |

### 响应字段

`results[]`，每项：

| 字段 | 说明 |
|---|---|
| `rerank_score` | 0–3，≥1.5 算优质结果 |
| `title` / `url` | 标题与链接 |
| `snippet` | 100–200 字短摘要，适合前端展示 |
| `summary` | 600–800 字长摘要，适合喂模型 |
| `content` | 正文（`need_content=false` 时为空） |
| `site_name` / `site_icon` / `date` | 站点与发布时间（UTC RFC 3339） |
| `authority` | 0–4 权威性，≥3 很权威，-1 未知 |

无匹配时返回空数组，不算失败。

---

## Fetch

```bash
curl https://api.deepseek.com/v1/tools/fetch \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com/article"}'
```

- 请求只有 `url`（≤8192 字符，必须带 host，不能带用户名密码）
- 响应：`{title, content}`，`content` 是 Markdown
- 受目标站点访问策略影响；抓不到就 404

---

## 计费与限速

| 项 | 价格 | 说明 |
|---|---|---|
| Search | 5 元 / 1000 次成功请求 | 只有 HTTP 200 且 results 非空才计费 |
| Fetch | 5 元 / 1000 次成功请求 | 必须返回正文才计费 |

- `count` 只影响返回条数，不影响单价
- 失败、无结果、超时都不计费
- QPS：Search 100 / Fetch 25（按账号，与 API Key 数量无关）；Fetch 还对目标域名单独限速

---

## 另一条路：Server 端工具

在 **Anthropic 兼容端点** `/anthropic/v1/messages` 里挂服务端工具，搜索在 DeepSeek 侧执行完再回答案：

```bash
curl https://api.deepseek.com/anthropic/v1/messages \
  -H "x-api-key: $KEY" -H "anthropic-version: 2023-06-01" \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-flash","max_tokens":800,
       "messages":[{"role":"user","content":"查一下今天的 DeepSeek 新闻"}],
       "tools":[{"type":"web_search_20260209","name":"web_search","max_uses":3}]}'
```

- 支持的 type：`web_search_20250305`、`web_search_20260209`
- **不支持** web_fetch 类工具（422 明确列出只认上面两种）
- 响应里会有 `server_tool_use`（搜索词）和 `web_search_tool_result`（结果列表），最后是 `text`
- `usage.server_tool_use.web_search_requests` 能看到实际搜了几次
- DSH / Claude Code / Codex 用的就是这条；**2026-11-01 00:00（北京时间）起开始计费**

---

## 本地封装

`~/bin/dstools.py`（源码见本仓库 `hermes/scripts/dstools.py`）：

```bash
dstools.py "查询"              # 结构化结果 + 摘要标记
dstools.py "查询" --count 20   # 条数
dstools.py "查询" --content    # 带正文（重）
dstools.py "查询" --sum        # 再让 deepseek-flash 汇总一次
dstools.py --fetch <url>       # 抓正文 Markdown
```

选择建议：

- 要**自己判断**哪条结果有用 → 用 Search 原始接口
- 要**直接读一篇**已知链接 → 用 Fetch
- 要**一句话结论 + 来源** → 用 server 工具那条（省一次本地汇总）

---

## 常见错误

| HTTP | 含义 | 处理 |
|---|---|---|
| 400 | 请求体不合法（如 count 越界） | 改参数，别重试 |
| 401 | Key 缺失/无效 | 换 Key |
| 402 | 余额不足 | 充值 |
| 403 | Fetch 被安全策略拒 | 换源 |
| 404 | Fetch 抓不到正文 | 换源或改用浏览器 |
| 429 | 超 QPS | 等一会儿再试 |
| 5xx/408 | 下游问题 | 退避重试 |
