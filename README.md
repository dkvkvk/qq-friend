# qq-friend

QQ 机器人搭建流程：AstrBot + SnowLuma / anowluna + ClinePass，大肥鱼人格。

> 这份文档记录的是 2026-10-27 至 2026-10-28 在第二台 LightVela 云电脑上真实跑通的流程。
> 仓库里不放任何密钥、token、密码、内网地址原文，凡是需要你自己填的地方都写成占位符。
> 模型切换和表情包安装已于 2026-10-28 14:05 验证完成，见步骤 5 和步骤 8；真实 QQ 发送仍需用户实测。

## 架构

```
QQ 小号
  ↓ OneBot v11
SnowLuma / anowluna（QQ 客户端，WebUI 在其界面里）
  ↓ 反向 WebSocket（见下文关键点）
AstrBot（聊天框架，面板 6185）
  ↓ OpenAI 兼容
ClinePass（模型提供方）
```

关键架构差异（踩过坑，务必先读）：
- AstrBot 的 aiocqhttp 是**反向 WS 服务器**：它等 OneBot 客户端连进来，需要 X-Self-ID 头握手。
- SnowLuma 原配置只有监听端、没有 wsClients，光配 AstrBot 一侧是连不上的。
- 做法：在 SnowLuma 的 `onebot.json` 里**新增**一个 wsClients 条目（不要删原有内容，先备份），指向 AstrBot 的反向 WS 地址，重启 SnowLuma 后生效。
- 本仓库 `config/onebot.example.json` 就是这个新增条目的模板，token、地址一律用占位符。

## 前置条件

- 一台长期在线的云服务器 / 云电脑，装好 Docker 和 Docker Compose。
- 一个 QQ 小号（只用小号，绝不用主号），SnowLuma 的安装、初始化、QQ 登录扫码由你本人在机器上做。
- 一个 ClinePass 密钥。密钥只填进 AstrBot 自身的提供方配置里，不要写进仓库、聊天记录或截图里。
- 不需要 NapCat（本流程因不稳定已弃用）、不需要百炼 key、不需要长期记忆。

## 步骤

### 1. 装 Docker

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git
sudo docker ps   # 注意：普通用户直接跑 docker 可能报 sock 权限错，须用 sudo
```

### 2. 起 AstrBot

示例见 `deploy/docker-compose.yml`。AstrBot 镜像以实际验证过的版本为准，面板在云电脑内访问 `http://127.0.0.1:6185`。

```bash
cd deploy
sudo docker compose up -d
sudo docker ps
sudo docker logs -f astrbot   # 初始面板密码在容器日志里，服务端内部读取，不要外发
```

面板登录失败的坑：如果在 VNC 里打字，带 Shift 的大写字母可能被送成小写，导致“用户名或密码错误”。
绕法：不要用 VNC 打字登面板，改用服务器内直接读日志、走面板 API，或由本人在机器上登录。

### 3. 装 SnowLuma / anowluna，登 QQ 小号

- SnowLuma 本体由你本人安装、初始化、扫码登录 QQ 小号，助手不自动下载、启动或控制它。
- 在它的 WebUI 里确认：服务运行中、在线账号 1 个、OneBot 的 HTTP 和 WS 都显示正常。
- 打开它的 `onebot.json`，核对 HTTP 和 WS 的监听端口、accessToken 是否已设置（只确认“已设置”，不要把 token 值贴出来）。
- 按 `config/onebot.example.json` 新增 wsClients 条目指向 AstrBot，备份原文件，重启 SnowLuma。

### 4. 在 AstrBot 里配 OneBot v11

- 面板里新增平台 onebot-v11，类型 aiocqhttp，反向 WS。
- 地址和 token 从 SnowLuma 的 `onebot.json` 里实测取得，不要猜端口、不要假设 HTTP 和 WS 同端口同 token。
- 验证：AstrBot 面板 stats 里 onebot-v11 为 running、错误数为 0；SnowLuma 日志里显示 WS-Client 已连接；AstrBot 日志里显示 aiocqhttp 适配器已连接。

### 5. 在 AstrBot 里配 ClinePass 模型

规则（用户定）：**只用 flash 版模型，哪个便宜用哪个**。flash 模型都有识图能力，基础看图聊天不需要再走百炼转述。

- 提供方类型：OpenAI 兼容
- base：`https://api.cline.bot/api/v1`
- 模型：见 `config/astrbot-provider.example.json`。已于 2026-10-28 从 deepseek-v4.1-flash-1017 切换到最便宜的 mimo-v2.6-flash，提供方测试 available、错误为空，无需重启。
- 提供方测试通了不等于 QQ 聊天端到端通了，后者要真在 QQ 上发消息验证。

### 6. 配大肥鱼人格

- 来源：whyever77/dafeiyu-astrbot 的 `persona/大肥鱼-人格.md`，v2.1，2026-10-19 修订启用。
  大肥鱼是 DeepSeek 蓝鲸的社区二创形象（“你这只吃白饭的蓝色大肥鱼”梗），非官方角色。
- 本仓库 `persona/大肥鱼-人格.md` 就是该文件原样，MIT 许可，转载已注明出处。
- 在 AstrBot 里新建人格，名字叫“大肥鱼”，把该文件 `---` 之后的全文逐字粘贴为系统提示词，不要删节、不要把 `---` 之前的说明文字也粘进去。
- 设为 OneBot 的默认人格，提供方选 clinepass。

### 7. 装插件

见 `plugins/README.md`。已验证：
- `astrbot_plugin_face_convert`：QQ 表情文字转换、草稿箱、标点归一。没有百炼 key 时语音转写会提示未配置，表情转换主功能正常，不用因此禁用它。
- `astrbot_plugin_schedule_awareness`：把真实定时任务注入系统提示词，让它不再笼统说没有日程。

跳过：bili_activity（重）、长期记忆 livingmemory（本地 Ollama 重、托管要 key）、NapCat。

### 8. 表情包（已验证）

选定来源：DejavuMoe/deepseek_wale_girl，104 张 DeepSeek 鲸鱼娘动态表情，GIF 512×512 透明底，MIT 许可。
见 `stickers/README.md`。机制：stealer v3.1.11 图库已播种 104 张，face_convert 不提供可发图库是此前“没有表情包”的原因。
注意：粗分类有 77 张落入 confused，按情绪自动匹配精度可能不完美，关键词检索更可靠；真实 QQ 发送仍需实测。

### 9. QQ 实测

- 私聊发一条日常消息：回话像不像大肥鱼、会不会自然表现出喜欢白饭、是不是一到三句短句为主。
- 发一个中括号表情名或 QQ 表情：看能不能变成真 QQ 表情。
- 问当天日程：看还会不会笼统说没有日程。
- 发一张图：flash 模型识图，看它能不能说出图里具体内容，而不是硬猜。

## 跳过的东西（有意不做）

- NapCat：不稳定，改走 SnowLuma。
- 长期记忆：本地 Ollama + bge-m3 和托管嵌入都不装，只用 AstrBot 自带会话记忆。
- 百炼：无 key，语音克隆、视觉、ASR、TTS 全跳过。
- B 站活动插件：重，跳过。

## 坑位清单

- qq-bridge：文件不要删。服务停了不等于停牢，它曾在杀掉 2 秒内被拉起新进程；用 systemctl 停后仍要复核，且开机自启仍开着时，重启后有恢复风险。
- 面板登录：VNC 下 Shift 大写可能变小写，见步骤 2。
- OneBot：AstrBot 是反向 WS 服务器，SnowLuma 必须新增 wsClients，见架构一节。
- 初始密码：曾出现在工具记录里，日志里是明文，后续建议轮换或清理日志。
- 第一个 LightVela 账号：不要动。曾误打开过 lightvela.com 的第一个号，只浏览、未改配置，随后切回第二个号 lightvela.ai。
- 密钥、token、密码：永远不要写进仓库、聊天记录、截图、日志公开处。

## 目录

- `README.md`：本流程
- `deploy/docker-compose.yml`：AstrBot 示例模板
- `config/astrbot-provider.example.json`：ClinePass 提供方模板（密钥用占位符）
- `config/onebot.example.json`：SnowLuma 新增 wsClients 模板（token 用占位符）
- `persona/大肥鱼-人格.md`：大肥鱼 v2.1 人格原文，来源见上文
- `plugins/README.md`：插件安装说明
- `stickers/README.md`：表情包来源与 stealer 安装（已验证）

## 致谢与出处

- AstrBot、SnowLuma / anowluna、ClinePass 各归其作者。
- 大肥鱼人格与插件思路来自 whyever77/dafeiyu-astrbot（MIT），本仓库仅作搭建记录与转载注明，不代表 DeepSeek 官方。
- 表情包来自 DejavuMoe/deepseek_wale_girl（MIT），仅自用、非商业。
