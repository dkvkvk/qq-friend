# 概念问答：VNC、OneBot、NapCat、qq-bridge

这篇是 2026-10-28 聊天里问答的整理版，不是原始聊天记录。
凡是密钥、token、密码、内网地址原文一律不写，只写占位符和“去哪里找”。

## VNC 是啥

**一句话：远程看电脑画面的技术，不是某个具体的软件，也不是 QQ。**

- VNC（Virtual Network Computing）是一套远程桌面协议（RFB），分两边：
  - 云电脑上跑 VNC **服务器**：把桌面画面发出来，收鼠标键盘。
  - 你这边用 VNC **客户端**：显示画面，把你的操作发回去。
- 它不是某一家公司的独家产品，RealVNC、TightVNC、TigerVNC 都是实现这个协议的不同软件。
- LightVela 云电脑产品里，后端就是在云电脑里跑了一个 VNC 服务器，
  前端给你包了一个网页版客户端（常说的 noVNC，不用装软件，浏览器打开 `<HOST>:6081` 那个页面就能看、能操作）。

### 常见误解

- **“VNC 打开了 QQ”**：不对。QQ 是直接装在云电脑操作系统上、跑在操作系统里的。
  VNC 只是因为这台电脑在机房里、你手边没显示器，才用来远程看它、操作它。
  没有 VNC，程序照样在后台跑，只是你看不见、点不到。
- **“进 VNC 还要再创建一个”**：创的不是新账号、也不是新 QQ。
  LightVela 账号只能证明“这台云电脑是你的”，它不会自动把密码传给 VNC；
  VNC 服务器在云电脑本地还有自己的一套验证，第一次用要单独给 VNC 设密码，之后用这个密码登录。
  如果云电脑被重建、VNC 配置被清掉，这个本地密码就没了，要重新设。
- **“没有 GUI 的系统才需要装 VNC 吗”**：反了，分两种：
  - 本来就有图形界面的系统：想远程看它，才需要 VNC（或 RDP 这类远程桌面办法），桌面本身不用再装。
  - 本来只有命令行的系统：光装 VNC 不够，因为根本没有画面可以传，得先装桌面环境，再装 VNC，缺一个都不行。
  - 完全不需要图形界面的程序（例如本仓库的 AstrBot + SnowLuma 机器人），GUI 和 VNC 都不需要，命令行就能跑。

## 云电脑、GUI、QQ、VNC 的关系

```
云电脑 = 一台完整的 Ubuntu（有浏览器、终端等软件）
  ├─ QQ / SnowLuma 等软件：直接装在操作系统上、跑在操作系统里
  └─ VNC 服务器：把这台电脑的桌面画面传出来
        ↓ 网络
      你的浏览器（网页版 VNC 客户端）：看到桌面、操作桌面
```

- 你在 VNC 里看到 QQ 登录界面，意思是：云电脑上那个 QQ 小号的会话当前没登录、在等扫码，
  或者桌面浏览器正好开着 anowluna 的网页、里面显示着登录二维码。显示的都是云电脑上小号的状态，不是你手机上主号的状态。
- VNC 关掉，云电脑上的程序还在后台跑；反过来，VNC 里看到登录界面，也不代表你本地 QQ 被登出了。

## OneBot 是啥

**一句话：机器人框架和 QQ 客户端之间约定的“通用语言”，不是 QQ 本身，也不是 AstrBot 本身。**

- 想让 AI 回 QQ 消息，中间得有个东西把两边连起来：
  QQ 那边收到消息了，怎么告诉 AI？AI 想回消息了，怎么发回 QQ？
- OneBot 就是规定这套对话格式的标准：消息来了叫事件，发送消息叫接口，
  文字、图片、表情、语音都拆成一段一段的消息段，格式都定死了。
- 它最早从 CQHTTP 演变来，现在最常用的是 v11 版，还有更新的 v12，但 v11 用得最广。

放在本仓库里：

```
QQ 小号 ←登录→ SnowLuma（协议端，真的收发 QQ 消息）
              ↓ OneBot v11（HTTP / 正向 WS / 反向 WS）
         AstrBot（框架，决定回什么）或 qq-bridge → DSH
              ↓
         大模型 API
```

- **正向 WebSocket**：协议端开服务，框架去连。
- **反向 WebSocket**：框架开服务，协议端去连。本仓库 AstrBot 那条就是反向 WS，见 `docs/combos/qq-two-paths.md`。
- **HTTP**：一问一答，最简单但没事件推送。

## NapCat 是啥

NapCat 也是实现 OneBot 的一个 QQ 端，和 SnowLuma 是同一个角色：登录 QQ、按 OneBot 格式收发消息，让 AstrBot 能接上 QQ。

差别在实现方式：

| | SnowLuma | NapCat |
|---|---|---|
| 本质 | 自己就是一个独立的 QQ 客户端实现 | 挂在官方新版 QQ（NTQQ）上的插件 / 注入层 |
| 依赖 | 不依赖官方 QQ 程序 | 必须先有官方 NTQQ 在跑 |
| 风险点 | QQ 版本更新会打断注入 | NTQQ 一升级、接口一变就容易跟着出问题 |
| 生态 | 新，文档少 | 老牌，遇到问题搜得到 |

本仓库的选择：用户称 NapCat 不稳定，改走 SnowLuma + AstrBot，NapCat 没装、也没接。
完整 NapCat 部署见 `docs/frameworks/napcat.md`，SnowLuma 见 `docs/frameworks/snowluma.md`。

## qq-bridge 是啥

qq-bridge 充当的角色和 AstrBot 的 OneBot 适配器一样：都是 OneBot 的消费端，只是大脑换成了 DSH。

```
QQ 小号 → SnowLuma → OneBot v11 → qq-bridge → DSH
                                  ↑ 独立桥接服务，不是 AstrBot 插件
                                  ↓ DSH 回的话
QQ 小号 ← SnowLuma ← OneBot v11 ← qq-bridge ← DSH
```

- 它的工程来源是 `derpyu520/qq-bridge`，本机工作区含 `config.json`、`state`、`src` 等。
- 它让 DSH 也能像 AstrBot 一样，通过 OneBot 跟 QQ 说话；DSH 那条线的优势是“能干活”（跑命令、改文件），不是只聊天。
- **不能和 AstrBot 同时抢同一条消息**：两边都开着，QQ 里会收到两份回复。
  现在的状态是 AstrBot 在跑、qq-bridge 服务 inactive、文件未删；切换路径前先停另一条，见 `docs/combos/qq-two-paths.md`。
