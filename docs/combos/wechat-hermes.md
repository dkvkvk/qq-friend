# 组合二：微信 + Hermes

本仓库在跑的那套。适合「想要一个能干活、还能聊天」的个人助手。

完整配置细节见 [`../hermes/README.md`](../hermes/README.md)。

## 总览

```
微信（iLink Bot）
   ↓ 消息
Hermes gateway（会话/投递/限流）
   ↓
agent 循环（工具 + 技能 + 记忆 + cron）
   ↓
模型 API（OpenAI 兼容）
```

## 步骤

### 1. 装 Hermes

```bash
hermes --version          # 确认可用
hermes gateway status     # 网关状态
```

### 2. 配模型

```bash
hermes config set model.default "cline-pass/deepseek-v4.1-flash-1017"
hermes config set model.provider custom
hermes config set model.base_url "https://api.cline.bot/api/v1"
hermes config set model.api_key "sk-xxx"
hermes -z "回一个 OK"      # 自检
```

> 用 ClinePass 时如果要识图，必须额外加 `providers.<name>.extra_body`，见 `hermes/README.md` 第 2.2 节。

### 3. 接微信

在 gateway 的配对流程里扫一次码，拿到 iLink token，配进 `platforms.weixin`。然后给它发一条消息，确认能回。

### 4. 写人格

`~/.hermes/SOUL.md`。三条必须写：

- 她是谁（身份、自称、口癖）
- 怎么说话（句长、黑名单、什么时候闭嘴）
- 边界（越权请求怎么拒，什么必须较真）

改完要**新开会话**才生效（系统提示缓存）。

### 5. 表情包

- 图放本地目录，`index.json` 记「图上的字 + 标签」
- 发送：`MEDIA:/绝对路径`
- 没索引的图先 OCR 再入库，否则只能瞎发

### 6. 定时任务

```bash
hermes cron list
hermes cron create "0 0-14 * * *" "每小时看抖音热榜" --name "抖音热榜" --deliver origin
hermes cron edit <id> --failure-deliver local
```

注意：
- cron 按时区解释，`TZ` 丢失会漂；用 `date` 和 `date -u` 对比
- monitor 脚本写裸文件名，放 `~/.hermes/scripts/`，stdout 必须确定性
- 微信 iLink 要求「对方最近给 bot 发过消息」，否则主动推送失败——这是最常见的「任务不推了」

### 7. 验收

1. `hermes -z "OK"` → 模型通
2. 发消息 → 有回复
3. 发一张图 → 它能描述内容
4. `hermes cron list` → 任务在，`last_status` 不是 error
5. 让它干一件实事（读文件 / 查网页）→ 能完成

## 与 QQ 方案的关键差异

| | 微信 + Hermes | QQ + AstrBot |
|---|---|---|
| 群里接梗 | 一般 | 强 |
| 干活能力 | 强（真终端、真文件） | 弱（要写插件） |
| 主动推送 | 受会话限制 | 只要在线就能发 |
| 封号风险 | 低 | 高（注入式） |
| 部署 | 一台机器 | 两个容器 + 扫码 |

## 常见故障

| 现象 | 处理 |
|---|---|
| 消息没回 | 看 gateway 是否在线，`hermes gateway status` |
| 定时任务不推 | 会话失效，让用户先发一条消息 |
| 图片看不懂 | 模型视觉路由没配对（`extra_body` 缺 `provider.order`） |
| 回复很慢 | 长任务在跑工具，或模型在推理 |
| 记忆混乱 | 记忆文件被写满，整理或清理旧条目 |
