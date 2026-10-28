# 表情包

## 选定来源（已验证，2026-10-28）

- 仓库：DejavuMoe/deepseek_wale_girl
- 内容：104 款 DeepSeek 鲸鱼娘同人动态表情
- 格式：GIF 512×512 透明底，另有 Telegram WebM（QQ 用 GIF 那份，不要用 WebM）
- 许可：MIT
- 目录：仓库里的 `gifs/` 目录

## 为什么之前说“没有表情包”

已安装的 face_convert 只把 `[流泪]` 这类方括号文字转换成 QQ 原生表情，
并不提供一个可发送的表情包图库。所以机器人说没有表情包是实话，
不是它在敷衍。修法是下面这套 stealer 图库，不是再装一个 face_convert。

## 实际发送机制：stealer（已安装、已启用、已播种）

- 插件：`astrbot_plugin_stealer` v3.1.11（插件市场版）
- 备份素材：容器内 `/AstrBot/data/stickers/dafeiyu/`，104 个 `.gif` 加情绪目录索引。
  注意：这个目录只是备份/素材，没有插件会自动从这里发送，实际发送走 stealer 图库。
- 播种格式（按插件官方协议，非猜测）：AstrBot MemePack v2，
  即 `memes/<分类>/` 图片目录 + `manifest.json`（包名/分类）
  + `semantic_metadata.json`（按文件名索引，含中文描述、短情绪名、tags、emotions、MIT 许可、署名与来源链接）。
  经插件 WebAPI 预检 104 项、8 类后导入完成。
- 图库验证：total=104，17 个情绪分类，scope 全部 public，来源 external:meme_pack。
- 发送工具：LLM 工具 `search_meme` / `send_meme` 已注册；
  `auto_send_meme=true`（已开），`steal_meme=false`（关闭，因未配视觉模型，避免偷图报错）。
  未配任何视觉模型（无 DashScope），只用预置元数据检索。
- 精度提醒：粗分类中有 77 张落入 confused，按情绪自动匹配的精度可能不完美，
  关键词检索是更可靠的测试方式。

## QQ 里怎么测

- 说「发一个表情包」或「来张表情包」，应触发 send_meme 发出一张鲸鱼娘 GIF；
  若再次出现“没有表情包”的原话，把原话反馈，以便查日志确认工具是否被调用。
- 说「发一个开心的表情」或「发个卖萌的贴纸」，验证按情绪/描述检索。
- 不依赖 LLM 的兜底指令：`/meme random` 随机试发一张；`/meme status` 查看图库统计；`/meme auto_on` 确认自动发送已开。

## 不做

- 不要用 Telegram 一键包当 QQ 包。
- 不要把 token、密钥写进任何配置文件示例里。
