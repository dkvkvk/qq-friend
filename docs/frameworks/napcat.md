# NapCat

QQ 协议端里的老牌选手：基于 NTQQ 客户端，把 QQ 翻译成 **OneBot 11**，自带 WebUI。

- 文档：<https://napneko.github.io/>
- 镜像：`mlikiowa/napcat-docker`

## 它干什么

```
QQ 客户端（登录一个真实账号）
   ↓ 注入
NapCat ← WebUI 配置
   ↓ OneBot v11（HTTP / 正向 WS / 反向 WS）
AstrBot / NoneBot2 / 自写服务
```

没有它，框架连不上 QQ；有了它，框架只负责聊天逻辑。

## 部署（Docker）

```bash
docker run -d --name napcat \
  -e NAPCAT_GID=0 -e NAPCAT_UID=0 \
  -p 3000:3000 -p 3001:3001 -p 6099:6099 \
  -v $PWD/napcat/config:/app/napcat/config \
  -v $PWD/qq:/app/.config/QQ \
  --restart unless-stopped \
  mlikiowa/napcat-docker:latest
```

- `6099` WebUI（看日志、扫码登录）
- `3000` HTTP，`3001` 正向 WebSocket（按需改）
- 首次启动去 WebUI 扫码登录

## 配 OneBot

WebUI → 网络配置 → 新建：

| 项 | 值 |
|---|---|
| 类型 | WebSocket 服务器（正向）或 反向 WS |
| 端口 | 3001 |
| 消息格式 | Array |
| Token | 强随机，和框架里填的一致 |
| 上报自身消息 | 开 |

## 和框架对接

- AstrBot：平台适配器选 `aiocqhttp`，填 `ws://napcat:3001`（同网络用容器名）
- NoneBot2：`ONEBOT_WS_URLS=["ws://napcat:3001"]`

## 坑

- **纯表情消息会被跳过**：框架收到的是空文本，看起来像「装死不回」
- **两套表情编号体系**：`[旺柴]` 这类文字要经过转换插件才发得出去
- **掉线不自愈**：进程在但会话断了，发消息没反应 → 看 WebUI 日志，必要时重启
- **QQ 版本敏感**：客户端升级后等 NapCat 跟进
- 群消息要额外开群事件上报，否则只收私聊

## 安全

- WebUI 和 OneBot 端口**不要**直接暴露公网，用 SSH 隧道或内网
- token 泄露=别人能用你的号发消息
- 用小号，控制发送频率，别群发

## 合规

第三方协议端，非官方接口。违反 QQ 用户协议，有封号风险。自用自担。
