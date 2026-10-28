# AstrBot

一站式聊天机器人框架，Python 写的，带 WebUI 和插件市场。群里像个人的那套基本都是它。

- 仓库：<https://github.com/AstrBotDevs/AstrBot>
- 支持平台：QQ、企业微信、微信公众号、飞书、钉钉、Telegram、Slack、Discord
- 形态：Docker 一键起，或者 pip 装

## 结构

```
平台适配器（OneBot / 公众号 / TG…）
        ↓ 事件
pipeline（@ 检测、唤醒、限流、知识库检索）
        ↓
插件（表情、语音、搜索、画图…）
        ↓
LLM（OpenAI 兼容接口都行）
```

## 部署（Docker，最省事）

```bash
docker run -d --name astrbot \
  -p 6185:6185 -p 6199:6199 \
  -v $PWD/data:/AstrBot/data \
  --restart unless-stopped \
  soulter/astrbot:latest
```

- `6185` WebUI，`6199` 给 OneBot 反向 WS 用
- 进 WebUI 配：模型（API Base + Key）、平台适配器、人格

## 接 QQ

两种配法，取决于谁开服务：

| 模式 | 谁开 WS | AstrBot 里填什么 |
|---|---|---|
| 正向 WS | 协议端（NapCat/SnowLuma）开 | 协议端地址 `ws://ip:3001` |
| 反向 WS | AstrBot 开 | 协议端填 `ws://astrbot:6199/ws` |

NapCat 和 SnowLuma 都只是协议端，接上哪个都行。

## 人格怎么配

在 WebUI 的「人格」里写系统提示词。要点和 Hermes 一致：

- 先身份，后说话方式，最后边界
- 群聊要写**回复频率**：默认不回，被点名或多轮相关才开口
- 别把安全规则放进知识库
- 人格改了要重启会话才生效

## 知识库

- 文档会被切块（约 512 字）+ 向量化，每条消息前检索命中再注入
- **一条一个条目**（一个梗一条、一个指令一条）比大段散文好检索
- 全局库对所有会话生效；私密内容走会话级绑定
- 人格（她是谁）/ 知识库（她会什么）/ 长期记忆（她记得什么）三件分开

## 插件（值得装的）

| 插件 | 作用 |
|---|---|
| `astrbot_plugin_face_convert` | 把 `[旺柴]` 这类文字变成真 QQ 表情 |
| `astrbot_plugin_schedule_awareness` | 把真实定时任务注入提示词，避免她说「我没有日程」 |
| 主动聊天 `proactive_chat` | 随机/沉默触发主动说话（要限制频率，容易 misfire） |
| 语音转写 / TTS | 语音消息进、语音条出 |

## 坑

- 纯表情消息会被整条跳过（她「装死不回表情」）
- 「消息回声病」：人格指令打不过她最近自己说过的话，得靠更强的人格约束或重开会话
- 主动聊天容易在不对的时机冒话，必须设触发条件
- 掉线不会自愈，配合协议端的重连

## 优点 / 代价

**优点**：多平台、插件生态强、WebUI 好上手、群聊体验最完整。

**代价**：它是「聊天机器人」，不是「能干活的 agent」——想让它跑命令、改文件，得写插件；没有原生的通用工具循环。
