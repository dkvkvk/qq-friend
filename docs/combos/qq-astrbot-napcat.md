# 组合一：QQ + AstrBot + NapCat

最主流的自建方案。适合「想在群里像个人」的场景。

## 总览

```
QQ 小号 ←登录→ NapCat ←OneBot WS→ AstrBot ←HTTP→ 大模型 API
                                    ↓
                              表情/语音/知识库插件
```

## 步骤

### 1. 准备

- 一个 QQ 小号（别用主号）
- 一台能跑 Docker 的机器
- 大模型的 API Base + Key

### 2. 起 NapCat

```bash
docker run -d --name napcat \
  -e NAPCAT_GID=0 -e NAPCAT_UID=0 \
  -p 3001:3001 -p 6099:6099 \
  -v $PWD/napcat/config:/app/napcat/config \
  --restart unless-stopped \
  mlikiowa/napcat-docker:latest
```

打开 `http://ip:6099` → 扫码登录 → 网络配置里建 **WebSocket 服务器**，端口 3001，消息格式 Array，设一个强 token。

### 3. 起 AstrBot

```bash
docker run -d --name astrbot \
  -p 6185:6185 -p 6199:6199 \
  -v $PWD/astrbot/data:/AstrBot/data \
  --restart unless-stopped \
  soulter/astrbot:latest
```

WebUI `http://ip:6185`：

1. 配模型：API Base / Key / 模型名
2. 加平台：`aiocqhttp`，地址填 `ws://napcat:3001`（同一 docker 网络）或 `ws://内网IP:3001`，token 对齐
3. 写人格

### 4. 人格

写清三件事：她是谁、怎么说话、什么时候不说话。

```
- 默认一句话，不超过两行
- 群里没点名、话题和我无关时，安静
- 被 @ 或提到名字必回
- 不总结、不升华、不说「我理解你的感受」
```

### 5. 装插件

- 表情转换（把 `[旺柴]` 变成真表情）
- 日程感知（把 cron 任务注入提示词）
- 语音转写（可选，要百炼或 whisper）

### 6. 验收

1. 私聊发「在吗」→ 有回复
2. 群里 @ 它 → 有回复
3. 发一个表情 → 它能接话（验证纯表情消息没被跳过）
4. 让它发一个 QQ 表情 → 看是不是真表情
5. 观察 30 分钟：会不会刷屏

## 常见故障

| 现象 | 原因 | 处理 |
|---|---|---|
| 完全没反应 | 协议端掉线 / WS 没连上 | 看 NapCat WebUI 日志，重连 |
| 私聊能回、群里不回 | 群事件没开 / 没被 @ | 开群上报，检查唤醒词 |
| 发出去没反应 | 会话断、频率限制 | 降低频率，重启协议端 |
| 表情发不出 | 编号体系不匹配 | 装表情转换插件 |
| 回复越来越长 | 上下文累积 | 限制历史轮数，或重开会话 |

## 运维建议

- 两个容器都 `--restart unless-stopped`
- 每天定时重启协议端（防内存泄漏和僵连接）
- 日志留 7 天足够
- 配置和人格进 git，别只存在容器里
