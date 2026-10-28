# 插件

来源：whyever77/dafeiyu-astrbot 的 `plugin/` 目录，MIT。

## 已安装并启用

- `astrbot_plugin_face_convert` v1.2.1
  - 作用：QQ 表情文字转换（中括号表情名变成真 QQ 表情）、草稿箱、标点归一。
  - 表情字典载入 326 条。
  - 没有百炼 key 时，语音转写会提示未配置，表情转换主功能正常，不用禁用。
- `astrbot_plugin_schedule_awareness` v1.0.0
  - 作用：把真实定时任务注入系统提示词，问日程时不再笼统说没有日程。

## 安装方法

1. 从原仓库 `plugin/` 目录把上述两个插件文件夹复制到 AstrBot 的 `data/plugins/`。
2. 重启 AstrBot 容器，启动日志里无 error / fail / traceback 才算加载成功。
3. 面板里确认两个插件均为启用状态。

## 跳过

- `astrbot_plugin_bili_activity`：重，跳过。
- 长期记忆、DashScope 语音 / 视觉 / TTS：无 key，跳过。
- NapCat：不稳定，跳过。
