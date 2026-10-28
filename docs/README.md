# 聊天智能体部署手册

按**平台**和**框架**两个维度分类，写清楚每条路的装法、代价和坑。

## 目录

| 文档 | 内容 |
|---|---|
| [platforms/qq.md](platforms/qq.md) | QQ：官方 Bot、OneBot 注入、协议库三条路 |
| [platforms/wechat.md](platforms/wechat.md) | 微信：公众号、企业微信、个人号 hook、iLink Bot |
| [frameworks/hermes.md](frameworks/hermes.md) | Hermes Agent（本仓库 `hermes/` 那套） |
| [frameworks/astrbot.md](frameworks/astrbot.md) | AstrBot：多平台机器人框架 |
| [frameworks/snowluma.md](frameworks/snowluma.md) | SnowLuma：NTQQ 注入式协议端 |
| [frameworks/napcat.md](frameworks/napcat.md) | NapCat：同为 QQ 协议端，生态最广 |
| [combos/qq-astrbot-napcat.md](combos/qq-astrbot-napcat.md) | 最流行组合的完整部署顺序 |
| [combos/wechat-hermes.md](combos/wechat-hermes.md) | 微信 + Hermes 的完整部署顺序 |

## 先想清楚三件事

1. **要不要进群**：进群才能和一群人接梗，但也意味着要面对群规、刷屏风险和封号风险。
2. **账号归谁**：用真账号（注入/协议）能力强但不合规；用官方 Bot 合规但能力受限。
3. **谁负责「智能」**：框架层（AstrBot）还是 agent 层（Hermes）。这决定你能不能让机器人干活，而不只是聊天。

## 选型矩阵

| | Hermes | AstrBot | SnowLuma | NapCat |
|---|---|---|---|---|
| 定位 | 通用 agent | 机器人框架 | QQ 协议端 | QQ 协议端 |
| 能不能自己动手（跑命令/改文件） | ✅ 强 | ⚠️ 插件能做到 | ❌ | ❌ |
| 多平台 | 微信/Telegram/Discord 等适配器 | QQ/企微/公众号/飞书/钉钉/TG/Slack | 只出 OneBot 接口 | 只出 OneBot 接口 |
| 需要真 QQ 账号 | ❌ | 取决于接入方式 | ✅ | ✅ |
| 封号风险 | 无（官方接口受限） | 随接入方式 | 高 | 高 |
| 群聊体验（表情/拍一拍/引用） | 一般 | ✅ 强 | ✅ 提供能力 | ✅ 提供能力 |
| 部署复杂度 | 低 | 中 | 中高 | 中 |
| 适合谁 | 想要「能干活」的助手 | 想要「群里像个人」 | 已有 AstrBot 等框架，缺协议端 | 同左，社区更大 |

## 常见组合（按推荐度）

1. **QQ + AstrBot + NapCat** — 生态最全，插件多，出了问题搜得到
2. **QQ + AstrBot + SnowLuma** — 新协议端，配置更轻，文档少一些
3. **微信 + Hermes** — 本仓库这套，能干活，聊天体验一般
4. **微信 + AstrBot（公众号/企微）** — 合规稳妥，但要认证主体
5. **QQ + Hermes** — 需要自己写 OneBot → Hermes 的桥，不推荐新手

## 通用铁律

- **协议端只是翻译器**，它不理解语言。所有「像不像人」都取决于框架里的人格提示词。
- **人格分三层**：人格（她是谁）／知识（她会什么）／记忆（她记得什么）。三件别混在一个提示词里。
- **别把安全规则放进知识库**——知识库内容会被当文档引用出来。
- **群聊必须有回复频率控制**，否则一定被嫌吵。
- 任何注入式方案都要准备**掉线重连**和**小号兜底**。
