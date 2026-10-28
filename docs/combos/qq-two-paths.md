# QQ 对话的两条路径

同一台云电脑、同一个 QQ 小号、同一个 SnowLuma 协议端，可以接出两条不同的对话路径。
区别只在“大脑”是谁：AstrBot，还是 DSH。

> 安全底线（两条路都适用）：只用 QQ 小号，绝不用主号；
> 密钥、token、密码一律只写占位符，不进仓库；
> 一个 QQ 号同一时间只能被一条路真正接管，否则两边都会回消息。

## 路径总览

```
路径 A（正在跑）：QQ 小号 → SnowLuma → OneBot v11 → AstrBot → ClinePass 模型
路径 B（已停用，文件未删）：QQ 小号 → SnowLuma → OneBot v11 → qq-bridge → DSH
```

| | 路径 A：AstrBot | 路径 B：DSH + qq-bridge |
|---|---|---|
| 大脑 | AstrBot 框架 + 人格 + 插件 | DSH（DeepSeek Harness）Agent |
| 协议端 | SnowLuma / anowluna | SnowLuma / anowluna（同一个） |
| 接口 | OneBot v11，反向 WebSocket | OneBot v11，经 qq-bridge 转发 |
| 人格 | 大肥鱼 v2.1（AstrBot 人格） | DSH 自己的 Agent 设定 |
| 表情包 | stealer 图库（见下） | DSH 侧无 stealer，需另配 |
| 语音 | 正在接 AstrBot QQ 语音（见可加项） | DSH 侧已接 FreeTTS MCP（只出 MP3 链接，不等于 QQ 语音） |
| 当前状态 | **正在跑** | **已停，服务 inactive，文件未删** |
| 适合 | 群里像个人、插件多、人格可控 | 能干活的 Agent、跑命令改文件 |

## 路径 A：QQ + SnowLuma + AstrBot（正在跑）

### 消息怎么走

```
你在 QQ 里发一句话
  ↓ SnowLuma 收到（QQ 客户端，WebUI 在 <HOST>:5099 那个界面里）
  ↓ OneBot v11 事件（反向 WS）
AstrBot 收到 → 过 pipeline（唤醒、限流）→ 调 ClinePass 模型
  ↓ 回复文本 / 表情 / 图片
OneBot v11 发送接口 → SnowLuma → QQ 小号发出去
```

### 关键点：反向 WS，别配反了

- AstrBot 的 aiocqhttp 是**反向 WS 服务器**：它等着协议端连进来。
- SnowLuma 原配置只有监听端、没有 wsClients，光配 AstrBot 一侧连不上。
- 做法：在 SnowLuma 的 `onebot.json` 里**新增**一个 wsClients 条目指向 AstrBot，
  先备份原文件（本仓库实测备份名格式为 `onebot.json.bak-<时间>`），重启 SnowLuma 后生效。
- 模板见本仓库 `config/onebot.example.json`，地址和 token 一律用占位符，
  必须从实际 `onebot.json` 里实测取得，不要猜端口、不要假设 HTTP 和 WS 同端口同 token。

### 配置流程

1. **准备**
   - 一台长期在线的云电脑，装好 Docker（本流程实测 Docker 29.x、Compose v2.x，须 `sudo` 用 docker）。
   - 一个 QQ 小号。SnowLuma 的安装、初始化、扫码登录由你本人在机器上做，助手不自动下载、启动或控制它。
   - 一个 ClinePass 密钥，只填进 AstrBot 自身的提供方配置里。
2. **起 AstrBot**
   - 模板见 `deploy/docker-compose.yml`，实测镜像 `soulter/astrbot:v4.29.0`，面板在云电脑内 `http://127.0.0.1:6185`。
   - 初始面板密码在容器日志里，服务端内部读取，不要外发；VNC 里打字可能把 Shift 大写送成小写导致登录失败，敏感登录改走服务端 API 或本人登录。
3. **配 SnowLuma**
   - WebUI 里确认服务运行中、在线账号 1 个、OneBot 的 HTTP 和 WS 都正常。
   - 按上文新增 wsClients，备份，重启 SnowLuma，QQ 重新登录重连。
4. **在 AstrBot 里配 OneBot**
   - 面板新增平台 onebot-v11，类型 aiocqhttp，反向 WS，地址和 token 与 SnowLuma 对齐。
   - 验证：面板 stats 里 onebot-v11 为 running、错误数为 0；SnowLuma 日志里 WS-Client 已连接。
5. **在 AstrBot 里配模型**
   - 提供方类型 OpenAI 兼容，base `https://api.cline.bot/api/v1`，模板见 `config/astrbot-provider.example.json`。
   - 规则（用户定）：**只用 flash 版模型，哪个便宜用哪个**；实测最便宜为 `cline-pass/mimo-v2.6-flash`，提供方测试 available、错误为空才算通。
   - 提供方测试通了不等于 QQ 端到端通了，要真在 QQ 上发消息验证。
6. **配人格**
   - 本仓库 `persona/大肥鱼-人格.md`，v2.1，2026-10-19 修订启用，来源 whyever77/dafeiyu-astrbot（MIT）。
   - 在 AstrBot 新建人格“大肥鱼”，把该文件 `---` 之后的全文逐字粘贴为系统提示词，不要把 `---` 之前的说明文字也粘进去，设为 OneBot 默认人格。
   - 2026-10-28 实测补充：人格末尾追加了一段表情包工具指令（v2.1 原文未动），要求要表情时必须先搜再发、永不说没有表情包、无结果换口语词重搜。
7. **装插件**
   - `astrbot_plugin_face_convert`：把中括号表情名变成真 QQ 表情。注意：它**不提供**可发送的表情包图库。
   - `astrbot_plugin_schedule_awareness`：把真实定时任务注入提示词。
   - `astrbot_plugin_stealer`：表情包图库，见下文。
8. **表情包**
   - DejavuMoe 104 张 GIF（MIT）按 MemePack v2 导入 stealer，图库 104 张。
   - aigengtu 143 张图 + OCR `index.json`（来源 aigengtu.com，社区二创，仅自用非商业，原为 Hermes 配过）：
     只导入 `safe=true` 的条目，排除 `safe=false`（含脏话 + 真人名）条目；100 张安全条目中两张内容 hash 相同被去重，实际入库 99 张。
   - 合计 stealer 图库 203 张（104 + 99）。WebP 经查 stealer 与 OneBot / NTQQ 原生支持，无需转换。
   - 实测教训：命令 `/meme random` 能发、对话一开始搜不到，是因为 stealer 相似度阈值（base_score < 0.15 丢弃）加旧标签太粗；
     修法是人格工具指令 + 带 OCR 标签的新包，服务端离线搜“摸鱼”已满分命中，真实 QQ 对话重测仍需用户确认。
9. **验收**
   - 私聊发日常消息：回话像不像大肥鱼、一到三句短句为主。
   - 发中括号表情名：能不能变成真 QQ 表情。
   - 说“发一个摸鱼的表情包”：应直接发出一张 WebP 贴纸，而不是说没有贴纸包。
   - 问当天日程、发一张图：分别验证日程注入和 flash 模型识图。

## 路径 B：QQ + SnowLuma + qq-bridge + DSH（已停用）

### 消息怎么走

```
你在 QQ 里发一句话
  ↓ SnowLuma 收到
  ↓ OneBot v11 事件
qq-bridge（独立桥接服务，不是 AstrBot 插件）收到 → 转发给 DSH
  ↓ DSH Agent 决定回什么（能跑命令、改文件，是“能干活”的那条线）
qq-bridge 转回 OneBot 发送接口 → SnowLuma → QQ 小号发出去
```

### 关键点

- qq-bridge 充当的角色和 AstrBot 的 OneBot 适配器一样：都是 OneBot 的消费端，只是大脑换成了 DSH。
- 它的工程来源是 `derpyu520/qq-bridge`，本机工作区含 `config.json`、`state`、`src` 等，**文件未删**。
- 当前状态：`qq-bridge.service` 为 inactive、unit 文件完好，但开机自启仍为 enabled，重启后有被拉起的风险，复核时要看服务状态和自启状态两个地方。
- **不能和路径 A 同时抢同一条消息**：两边都开着，QQ 里会收到两份回复。要切换路径，先停另一条，再起这一条，并复核只剩一条在跑。

### 配置流程（按原工程思路，恢复时照此核对）

1. 确认 SnowLuma 已登录 QQ 小号、OneBot 正常，记下 HTTP / WS 地址和 accessToken（只确认“已设置”，不贴值）。
2. 确认 qq-bridge 工作区和配置文件在原位置，备份后再改，不要删文件。
3. 在 qq-bridge 配置里填 SnowLuma 的 OneBot 地址和 token、DSH 的接入地址，启动服务并看日志：SnowLuma 侧已连接、DSH 侧已收到事件。
4. 在 QQ 私聊发“在吗”验证：只应收到 DSH 那一份回复；若同时收到 AstrBot 的回复，说明路径 A 没停干净，先停 AstrBot 那条再测。
5. 切换回路径 A 时反向操作：停 qq-bridge（并复核 inactive），确认 AstrBot 的 OneBot 仍为 running、错误数为 0，再在 QQ 里重测。

## 两条路怎么选、怎么切换

| 场景 | 选哪条 |
|---|---|
| 群里聊天、要人格、要表情包、要插件 | 路径 A：AstrBot |
| 让它在云电脑上干活、跑命令、改文件 | 路径 B：DSH + qq-bridge |
| 两条都想要 | 分会话 / 分群接管，不要同一条消息两边都接 |

切换检查清单（每次切换都做一遍）：
- [ ] 另一条路的服务已停（`systemctl status` 看到 inactive）
- [ ] 本条路的 OneBot 已连接（AstrBot 面板 running、err=0，或 qq-bridge 日志已连接）
- [ ] QQ 私聊只收到一份回复
- [ ] 模型 / 人格 / 插件没有被切换动作误改

## 可加项（按状态分）

### 已装

- face_convert、schedule_awareness、stealer + 两套表情包（见上文）
- DSH 侧 FreeTTS MCP：`https://mcp.freetts.org/mcp`，DSH 里说“用 FreeTTS 把××读出来”即可出 MP3 链接；
  无账号实测单次 2000 字、每天 2000 字、每分钟 10 次、仅标准音色、仅 MP3、文件只保留 1 小时，末尾带广告口播；
  免费账号可提至每天 5000 字，去广告只在 PRO 付费档。**注意：这只是 DSH 的 MCP，不等于 QQ 语音。**

### 进行中

- **AstrBot QQ 发语音**：正在接，方向是先查 AstrBot 自带 TTS / 插件与 OneBot 语音段格式，
  能直连 FreeTTS 就用 FreeTTS，不能就用内置免费 TTS；中文女声、只在明确要求时发语音。
  在回结果前，不要声称 QQ 已能发语音。

### 可加（未装，按需选，不用全装）

- 多个人格卡 / 按会话设不同人格
- 课程记忆教学模板（原仓库的教学模板思路）
- 主动任务：定时提醒类（例如 23:30 晚安、07:00 起床），需限制频率
- 群聊规则：私聊必回 vs 群里 @ / 引用 / 唤醒词（如“大肥鱼”）、白名单、回复频率
- 链接解析插件（市场链接解析）、音乐点歌、拍一拍反应插件（装后要关掉它默认的定时拍一拍任务）
- 运维清理：关 qq-bridge 开机自启、AstrBot 配置与人格备份、重启检查
- DashScope 语音 / 视觉 / TTS：需要 key，未装
- 长期记忆：本地 Ollama + 嵌入模型（重）或托管嵌入（需 key），未装，只用 AstrBot 自带会话记忆
- 知识库：热梗词典等，需要嵌入模型
- 图片生成：omnidraw 等，需要视觉 / 绘图模型
- B 站活动插件：重，不推荐
- FreeTTS 免费账号升级：每天 2000 → 5000 字，需用户自己注册，助手不代注册

### 明确跳过

- NapCat：用户称不稳定，改走 SnowLuma（见 `docs/frameworks/napcat.md` 对照）
- 长期记忆、DashScope、B 站活动：见上文，原因分别是重、需 key、重
