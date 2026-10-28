# Hermes Agent

通用 agent：聊天只是入口，重点是它能跑命令、改文件、开浏览器、跑定时任务。

完整配置实录见 [`../hermes/README.md`](../hermes/README.md)。

## 结构

```
平台适配器（微信/Telegram/Discord…）
        ↓
gateway ── 会话、投递、限流
        ↓
agent 循环 ── 工具调用 / 技能 / 记忆 / 定时任务
        ↓
模型 API（OpenAI 兼容即可）
```

关键点：**人格、工具、记忆是三个独立文件**

| 文件 | 作用 |
|---|---|
| `~/.hermes/SOUL.md` | 人格（她是谁、怎么说话） |
| `~/.hermes/skills/` | 技能（可复用的流程） |
| `~/.hermes/memories/` | 记忆（跨会话的事实） |
| `~/.hermes/config.yaml` | 模型、平台、审批策略 |
| `~/.hermes/cron/` | 定时任务与运行记录 |

## 最小可用配置

```bash
# 模型
hermes config set model.default "cline-pass/deepseek-v4.1-flash-1017"
hermes config set model.provider custom
hermes config set model.base_url "https://api.cline.bot/api/v1"
hermes config set model.api_key "sk-xxx"

# 平台（以微信为例，配对在 gateway setup 里做）
hermes gateway status
hermes gateway install   # 可选：装成系统服务

# 自检
hermes -z "回一个 OK"
```

## 人格文件怎么写

- 先写「她是谁」，再写「怎么说话」，最后写「边界」
- 说话规则要可执行：「默认一句话，别超过三行」比「说话简短一点」有用
- 加黑名单：`首先/其次/综上所述`、`作为AI`、`希望这个回答对你有帮助`
- 别在人格里塞知识——知识放技能或词典文件，按需查
- 改完要在**新会话**里生效（系统提示缓存）

## 定时任务

```bash
hermes cron list
hermes cron create "0 9 * * 1" "每周一检查 X" --name "X 周检" --deliver origin
hermes cron edit <id> --failure-deliver local
```

- cron 表达式按时区解释，容器 `TZ` 丢失时会漂；用 `date` 与 `date -u` 对比确认
- monitor 脚本只写裸文件名（放 `~/.hermes/scripts/`），stdout 必须确定性输出
- 无变化输出 `NO_CHANGE`，有变化输出 `NEW_...` + 明细

## 优点 / 代价

**优点**：能真正干活；技能会积累；记忆和人格可版本化；一条命令换模型。

**代价**：聊天体验不如专门的群聊框架（表情、拍一拍、引用这些要自己补）；接入平台受官方接口限制；没有按会话隔离记忆。
