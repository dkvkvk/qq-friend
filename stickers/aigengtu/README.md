# 大肥鱼表情包 · aigengtu 合集

来源：<https://aigengtu.com/archive>（DeepSeek 表情包大全，社区二创，SFW 收录）
抓取：手动入库 + `~/.hermes/scripts/aigengtu-stickers.py` 周更脚本（按 archive 列表比对 id，增量下载）

## 内容

- 143 张图：`001-131` 为早期 WebP，`239` 起部分为 PNG 原图（单张 2–4MB）
- `index.json`：每张图的 OCR 文字 + 标签 + 备注，键为文件名去扩展名
  - 结构：`{"2692": {"text": "...", "tags": ["白饭梗","催干活"], "note": "..."}}`
  - OCR 由 `cline-pass/deepseek-v4.1-flash-1017` 完成（该模型支持图片输入，请求需带 `"provider": {"order": ["deepseek"]}` 才能识别）

## 命名

文件名 = 站点 meme id，三位补零；同一 id 只存一份，扩展名可能是 `.webp` 或 `.png`。

## 授权

社区二创，站点本身免费公开收录，仅供自用、非商业。若用于发布或商用，请先联系原作者。

## 增量更新

```bash
python3 ~/.hermes/scripts/aigengtu-stickers.py   # 输出 NO_CHANGE 或 NEW_STICKERS <n>
```

脚本只比对 archive 前三页的 id，单次最多下 8 张，避免一次拉爆图库。
