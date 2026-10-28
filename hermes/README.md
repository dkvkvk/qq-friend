# Hermes Agent 配置实录（微信端大肥鱼）

> 目的：把这套「Hermes + 微信 + ClinePass 模型 + 大肥鱼人设 + 表情包库」的搭建过程写清楚，
> 换台机器能照着复现，或者对照排查。
> 记录时间：2026-10-28。文中 API key 一律用占位符。

---

## 0. 它和 AstrBot + SnowLuma + NapCat 那套的区别

| | AstrBot 栈 | 这套（Hermes） |
|---|---|---|
| 接入 | SnowLuma/NapCat 注入真 QQ 客户端，出 OneBot v11 | 微信 iLink Bot 官方接口，不用登录客户端 |
| 定位 | 群聊机器人框架 | 通用 agent，聊天只是入口 |
| 强项 | 群里接梗、表情、语音、认人 | 跑命令、改文件、开浏览器、定时任务 |
| 人格 | prompt + 插件 | `SOUL.md` + skills + memory |
| 风险 | 封号、掉线、跟 QQ 版本 | 会话/频率限制（见第 4 节） |

一句话：那套是「把 AI 塞进 QQ 群」，这套是「把 AI 放在机器上，微信只是对讲机」。

---

## 1. 环境

- Linux 主机，Python 3.12+（Hermes 自带运行时）
- 出网必须走代理：`HTTP_PROXY` / `HTTPS_PROXY`
  - 直接 TLS 会失败（curl rc=35）
  - Python 的 urllib/requests 走同一代理容易超时 → **网络 IO 一律 shell out 到 curl**
- Hermes 安装：`hermes --version`，配置目录 `~/.hermes/`

---

## 2. 模型接入（ClinePass）

### 2.1 基本配置

```bash
hermes config set model.default "cline-pass/deepseek-v4.1-flash-1017"
hermes config set model.provider custom
hermes config set model.base_url "https://api.cline.bot/api/v1"
hermes config set model.api_key "sk-你的key"
```

ClinePass 是 OpenAI 兼容网关，所以 `provider: custom` 即可，不用写适配器。

### 2.2 识图（关键，容易踩）

`deepseek-v4.1-flash` 本身**支持图片输入**（OpenRouter 元数据：`input: text, image`），但这个网关默认路由会落到 Vercel，**图片被静默丢掉**，只回：

```json
{"error":"empty response content","success":false}
```

解法：请求体里强制 DeepSeek 路由。

```bash
# 自定义 provider + extra_body
hermes config set providers.clinevision.base_url "https://api.cline.bot/api/v1"
hermes config set providers.clinevision.api_key "sk-你的key"
hermes config set providers.clinevision.api_mode chat_completions
hermes config set providers.clinevision.extra_body '{"provider":{"order":["deepseek"],"allow_fallbacks":true}}'
hermes config set auxiliary.vision.provider clinevision
hermes config set auxiliary.vision.model "cline-pass/deepseek-v4.1-flash-1017"
```

裸 curl 等价写法：

```bash
curl -s https://api.cline.bot/api/v1/chat/completions \
  -H "Authorization: Bearer $KEY" -H 'Content-Type: application/json' \
  -d '{"model":"cline-pass/deepseek-v4.1-flash-1017",
       "provider":{"order":["deepseek"],"allow_fallbacks":true},
       "max_tokens":1200,
       "messages":[{"role":"user","content":[
         {"type":"text","text":"图里写的是什么？"},
         {"type":"image_url","image_url":{"url":"data:image/jpeg;base64,..."}}]}]}'
```

### 2.3 另外两个坑

- **响应包装**：这个网关把结果包在 `{"data": {...}}` 里，Hermes 自带 `vision_analyze` 按 OpenAI 顶层结构解析会报
  `invalid response ... Expected object with .choices[0].message`。用 `see.py`（第 8 节）绕过。
- **余额**：非 `cline-pass/` 前缀的模型走的是按量计费，余额为 0 时报 `insufficient_credits`；
  走 `cline-pass/` 别名的请求不受此限。

---

## 3. 人设（SOUL.md）

`~/.hermes/SOUL.md` 是人格文件，新会话开始时加载（改完要新开会话才生效，因为系统提示已缓存）。

来源：<https://aigengtu.com/persona> 的 26 张社区卡，选的是「群傲娇鲸鱼 · 白饭万岁」（4444 字）。
原卡备份：`~/.hermes/personas/aojiao-whale-baifan.txt`。

改造要点（群聊 → 一对一私聊）：

- 删掉「判断这句话是不是对我说的」「拍一拍」「回复频率」这类群聊规则
- 保留：深海王族自称、白饭梗、傲娇嘴硬、口癖、破功瞬间
- 加：分寸（提醒一遍就够）、说话自觉（真心话才说）、不许嘴上干活（说去查就必须真调工具）、表情品味、不装懂
- 加：日程感知（被问定时任务先 `hermes cron list` 查真实列表）
- 加：热梗词典路径 `~/.hermes/kb/regan-dict.md`

> 社区经验：与其在输出端裁剪语气，不如往记忆里写「她自己琢磨出来的课程」——被召回时她会当成自己本来就懂的，比外部规则更管用。

---

## 4. 微信接入与投递

- 平台：微信 iLink Bot（`platform: weixin`），配置在 `~/.hermes/config.yaml` 的 `platforms.weixin`
- **硬约束**：bot 主动发消息需要该 peer 最近给 bot 发过消息，否则

```
iLink sendmessage session not ready: ret=-2 ... prepare failed
```

  也就是说：**定时任务的推送会因为你长时间没说话而失败**，只要有新消息进来就恢复。
- 失败时不要把 `failure_deliver` 设成 `origin` 反复重试刷屏；设成 `local` 只记日志更稳。

```bash
hermes cron edit <job-id> --failure-deliver local
```

---

## 5. 表情包流水线

- 站点：<https://aigengtu.com/archive>（DeepSeek 表情包大全，社区二创）
- 目录：`~/dy-trending/whale/`，文件名 = 站点 meme id（三位补零）
- 元数据：`index.json`，键为文件名去扩展名，值 `{text, tags, note}`，text 是图上的字（OCR 得来）
- 抓取：`~/.hermes/scripts/aigengtu-stickers.py`
  - 扫 archive 前 3 页的 id，和本地/状态文件比对，只下新的，单次最多 8 张
  - 老图是 `.webp`，新图是 `.png`，两种都试
  - **必须校验文件头**（RIFF/WEBP、PNG、JPEG）：404 会以 200 返回一个 HTML 错误页，只看状态码会把错误页当图存进去
  - 状态文件：`~/.hermes/state/aigengtu-stickers.json`
- 发送：直接 `MEDIA:/绝对路径`，微信端当图片发出
- 索引：新图入库后跑 `see.py` OCR，写进 `index.json`（一张约 5 秒）

配套定时任务见第 6 节。

---

## 6. 定时任务

| 任务 | 表达式 | 说明 |
|---|---|---|
| 抖音热榜 | `0 0-14 * * *` | 每小时，对应北京时间 08:00–22:00（调度器按 UTC 解析时） |
| X 热榜 | `0 0 * * *` | 每天一次 |
| AIHOT 日报 | `0 1 * * *` | 每天一次 |
| 英语输入法提醒 | `0 7 * * *` | 每天一次 |
| 大肥鱼表情包周更 | `0 9 * * 1` | 每周一，带 monitor 脚本 |

**时区坑（重点）**：这套调度器按时区解释 cron 表达式，而容器的 `TZ` 变量可能在重启后丢失，
导致同一条表达式在北京时间和 UTC 之间切换——表现是「半夜推送」或「该推的时候不推」。
排查办法：`date` 和 `date -u` 对比，如果一致说明系统时钟就是 UTC，此时 `0 0-14` = 北京 08:00–22:00。

monitor 脚本约定：

- 脚本放 `~/.hermes/scripts/`，cron 里只写**裸文件名**（绝对路径会被拒）
- 脚本 stdout 是变更检测信号，**必须确定性输出**：不许带时间戳、不许随机顺序
- 无变化输出 `NO_CHANGE`，有变化输出 `NEW_...` 加明细

---

## 7. 搜索与抓取

### 主力：DeepSeek 官方 Search / Fetch

```
POST https://api.deepseek.com/v1/tools/search   # {query, count, need_content}
POST https://api.deepseek.com/v1/tools/fetch    # {url} → Markdown
```

- 自研搜索引擎，返回结构化结果（标题/URL/摘要/正文/日期/权威性/rerank）
- 支持 `site:`、`lang:`、`after:`、`before:`、精确短语
- 各 5 元 / 1000 次成功请求，失败或空结果不计费
- 详细字段见 `docs/reference/deepseek-search.md`

封装：`~/bin/dstools.py`

```bash
dstools.py "查询" [--count 8] [--content] [--sum]
dstools.py --fetch <url>
```

### 兜底：自建无 key 搜索

`~/bin/websearch.py "查询词" [条数]` —— 中文走搜狗，英文兜底 DuckDuckGo lite。
官方接口限额、报错，或不想花那 5 元时用。

### 抓取 + 提炼（不消耗 Search 额度）

`~/bin/fetch.py <url> [--sum]`：curl 抓页面、剥标签出正文，`--sum` 再让 deepseek-flash 提炼要点。

> Hermes 自带的 `web_search` 免费后端返回过完全不相关的外语结果，不可信，只作最后兜底。

---

## 8. 辅助脚本

| 脚本 | 用途 |
|---|---|
| `~/bin/see.py <图片> [问题]` | 图片 OCR/理解，走 ClinePass + 强制 deepseek 路由 |
| `~/bin/websearch.py "词" [n]` | 搜狗 + DDG 搜索 |
| `~/.hermes/scripts/aigengtu-stickers.py` | 表情包增量抓取（周更任务的 monitor 脚本） |
| `~/dy-trending/collect*.py` | 抖音 / X / AIHOT 数据采集，供对应 cron 任务使用 |

脚本源码见本仓库 `hermes/scripts/`（key 已替换为占位符）。

---

## 9. 换机恢复清单

1. 装 Hermes，确认 `~/.hermes/` 生成
2. 跑第 2 节的模型配置四连（含 `extra_body`）
3. 配微信平台凭据（iLink 账号），`hermes gateway status` 确认在线
4. 放人设：`SOUL.md` + `~/.hermes/personas/` 里的卡
5. 放表情库：`~/dy-trending/whale/`（本仓库 `stickers/aigengtu/` 即全量）+ `index.json`
6. 放脚本：`~/bin/see.py`、`~/bin/websearch.py`、`~/.hermes/scripts/aigengtu-stickers.py`
7. 建 cron 任务（第 6 节），时区先确认
8. 验收：`hermes -z "回一个 OK"`、发一张图让它 OCR、跑一次抖音采集脚本

---

## 10. 已知问题

- **视觉**：`vision_analyze` 用不了（响应包装问题），只能走 `see.py`
- **语音输入**：没接 ASR，收到的语音消息无法转写
- **记忆隔离**：全局记忆，没有按会话/按群分账（AstrBot 那边是 livingmemory 会话作用域）
- **推送可达性**：微信 iLink 需要用户先发消息激活会话，长时间静默后首次推送可能失败
- **搜狗跳转链接**：结果是 `sogou.com/link?url=...`，需要跟一次重定向才是原站地址
