---
name: viral-vending-machine
description: 爆款贩卖机 - 自媒体文案生成系统。按用户人设与案例库风格生成主题文案，支持对标博主/方向自动采集、口播转写、选题分析、防洗稿把关。Use when the user asks to 写文案/写笔记/写稿、按人设出内容、对标某个博主、扒某个方向的内容、更新案例库、让AI写小红书/抖音/公众号文案。Do NOT activate for 纯闲聊、与文案写作无关的问题。
metadata:
  version: 0.3.0
  tags: [自媒体, 文案, 小红书, 抖音, 爬虫, copywriting, content]
---

# 爆款贩卖机 Viral Vending Machine · 自媒体文案生成系统

按人设 + 案例库风格生成原创文案；可对标博主/方向自动采集并更新案例库。

## 三场景编排

### 场景A 写文案（核心）
1. 确认平台（小红书/抖音/公众号，默认让用户选或按主题推断）。
2. 读取 `assets/persona.md` 掌握人设。若仍含 `（` 占位符（未填写），先请用户提供人设再生成。
3. 读取 `references/originality.md` 掌握防洗稿红线（生成前必读）。
4. **读取 `references/style-guide.md` 掌握表达形式规范（必读）：选内容形式（揭秘/避坑/清单/金句/反差/观点）→ 套开头钩子 → 正文结构 → 语言特征 → CTA → 输出格式。**
5. **检索 `assets/hooks/` 标题库/钩子库**（按选题类型挑 1-2 个参考），读取 `assets/cases/index.md` 选 1-2 个最贴近的博主，读其 `assets/cases/<博主名>.md` 挑 2-3 条案例做风格示例。若库为空，仅依人设 + 平台规则生成。
6. 读取 `references/frameworks.md` 中匹配博主的选题方向/框架 → 纳入。
7. 按 `references/platform-rules.md` + `style-guide.md` 生成 **3-5 条不同角度**的完整文案。
8. 每条按 style-guide 第七节格式交付（标题/形式/主要观点/口播脚本/话题标签）。
9. 按 `references/originality.md` 自检 + `scripts/similarity.py`，不通过则改写。
10. **发布前总检**：运行 `python scripts/prepublish_check.py --file <文案> --platform <平台> --title "<标题>" --refs <案例库目录>`（AI味+违禁词+字数+标题+洗稿），不通过则改写后重检。

### 场景B 对标（自动采集）
1. 解析用户给的账号链接或关键词（判断平台：xhs/dy）。
2. **采集**（按平台选脚本）：
   - 小红书：`python scripts/collect.py --platform xhs --mode creator|search --target <ID或关键词> --count <N默认10>`
   - 抖音：`python scripts/douyin_api.py [sec_user_id] [count] [months]`（需 Chrome CDP 已登录抖音，`--remote-debugging-port=9222 --remote-allow-origins=*` 启动；从 Chrome 取 cookie 直接调抖音 API，绕过 MediaCrawler 签名 bug；支持按近 N 个月过滤）
   - 抖音 sec_user_id 提取：博主主页链接 `douyin.com/user/<sec_user_id>` 或纯 ID（`MS4wLjAB...` 开头）；纯抖音数字号（如 41470367）需先解析出 sec_user_id。
3. 若为抖音且目标是口播脚本类视频：运行 `python scripts/transcribe.py --json <输出>` 转写口播 → 再运行 `python scripts/enhance_transcript.py --json <输出> --remove-fillers --split` 做专名修正+删气口+分段（转写质量增强）。
4. 分析选题方向 → 追加到 `references/frameworks.md`（新博主加一章）+ 深度结论写入 `assets/knowledge/对标/<博主>.md`。
5. 运行 `python scripts/update_library.py --json <输出> --framework <赛道>` 更新案例库（生成 `assets/cases/<博主>.md` + 索引）。
6. 运行 `python scripts/update_hooks.py` 刷新标题库/钩子库（从新案例自动提取）。
7. 告知用户已入库，询问是否立即生成。

### 场景C 更新案例库
1. 读 `assets/cases/index.md` 拿全部对标博主清单。
2. 逐个重新采集（场景B第2步）→ 转写 → 入库（source_id 幂等，只追加新案例）。
3. 运行 `python scripts/update_hooks.py` 刷新标题/钩子库。
4. 汇总报告：更新了几个博主、新增几条。

> 注：脚本（collect/douyin_api/transcribe/enhance_transcript/update_library/update_hooks/similarity/prepublish_check/deai/compliance）尚未就绪时，可用 `references/frameworks.md` 与 `assets/cases/` 手动收集，不硬依赖脚本。
> 抖音采集依赖 Chrome CDP 登录态：启动命令 `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<固定目录>`，登录后 cookie 持久化。

## 硬规则
- **防洗稿最高优先**：见 `references/originality.md`。生成前必须读它。
- **发布前必须过 prepublish_check**：AI味/违禁词/洗稿三项任一失败，不得交付。
- 学习选题/角度/结构，不复制原句。连续 6+ 字相同必须改写。
- 用户给了人设后，如 `persona.md` 仍是模板占位符（含 `（`），先请用户提供人设再生成。
- 采集脚本失败时明确报错，不静默降级。
- 所有脚本用正斜杠路径，脚本在 `scripts/` 目录下用 `python scripts/xxx.py` 调用。

## 参考
- 平台规则: `references/platform-rules.md`
- 防洗稿: `references/originality.md`
- **表达形式规范（必读）: `references/style-guide.md`**
- **去AI味规则库: `references/deai-rules.md`**
- **违禁词库: `references/banned-words.md`**
- 写作框架/选题方向: `references/frameworks.md`
- 案例库: `assets/cases/`（index.md 索引 + 每博主一文件）
- 标题/钩子库: `assets/hooks/`
- 知识库: `assets/knowledge/`（对标/复盘/选题落盘）
