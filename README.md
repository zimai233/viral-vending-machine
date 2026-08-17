# 爆款贩卖机 Viral Vending Machine · 自媒体文案生成 Skill

> 投一个主题，吐一篇爆款文案。按你的**人设** + **对标案例库**生成原创文案，支持对标博主自动采集、口播转写、选题分析、防洗稿把关。全程对话操作，无感使用。

## 它能做什么

| 你说 | 效果 |
|---|---|
| 写个关于 XX 的文案 | 按人设+案例库出 3-5 条原创文案（含标题/观点/口播脚本/标签） |
| 对标 @某博主（或贴链接） | 自动扒取该博主近 N 个月高赞视频 → 转写口播 → 更新案例库 |
| 扒一下"XX"方向 | 按关键词采集热门内容 |
| 更新案例库 | 重扒所有对标账号的最新高赞内容（幂等去重） |

## 核心能力

- **人设驱动**：`assets/persona.md` 定义"你是谁、怎么说话"，生成时强制贴合
- **案例库**：`assets/cases/` 每对标博主一文件，含口播全文+框架标签，新博主自动追加
- **表达规范**：`references/style-guide.md` 沉淀的六大内容形式（揭秘/避坑/清单/金句/反差/观点）+ 开头钩子 + 正文结构 + 语言特征 + CTA
- **抖音口播规范**：`references/short-video-copywriting.md` 专门约束前3秒/前5秒、口播节奏、字幕画面、标题话题、评论 CTA、情感合规和数据复盘
- **防洗稿**：`scripts/similarity.py` n-gram 相似度检测，超标自动提示改写
- **去AI味**：`scripts/deai.py` AI痕迹评分（模板连接词/空话/翻译腔识别）+ 保真合同锁定事实
- **合规检测**：`scripts/compliance.py` 三级违禁词检测（硬性/风险/擦边），`references/banned-words.md` 可编辑词库
- **发布前总检**：`scripts/prepublish_check.py` 一键检查 AI味/违禁词/字数/标题/洗稿，不通过不放行
- **口播转写增强**：`scripts/enhance_transcript.py` 专名修正（glossary.tsv）+ 删气口 + 分段
- **钩子/标题库**：`assets/hooks/` 自动从案例库沉淀，生成时检索复用
- **知识库**：`assets/knowledge/` 对标分析/复盘结论落盘，跨任务决策有据可依
- **采集管线**：抖音直连 API（绕开 MediaCrawler 签名 bug）+ 口播 Whisper 转写

## 安装（新电脑）

**前置**：Python 3.11+、uv、ffmpeg、Node 16+、Git Bash（Windows）或 bash（macOS/Linux）、Chrome

```bash
# 1. 把 skill 放进 opencode 的 skills 目录
#    Windows:  %USERPROFILE%\.config\opencode\skills\viral-vending-machine\   或项目内 .opencode\skills\
#    macOS/Linux: ~/.config/opencode/skills/viral-vending-machine/

# 2. 一键初始化（装依赖 + clone MediaCrawler + Chrome 登录引导）
bash scripts/setup.sh

# 3. 填写你的私人数据（人设 + 案例库）
#    assets/persona.md           ← 你的写作人设
#    assets/cases/               ← 你的对标案例库

# 4. 配置 Chrome 调试（抖音采集用，一次性）
#    chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=<固定目录>
#    登录抖音后 cookie 持久化，之后采集自动复用
```

## 结构

```
viral-vending-machine/
├── SKILL.md              # 三场景编排（写文案/对标采集/更新案例库）
├── assets/
│   ├── persona.md        # 人设画像（用户数据）
│   └── cases/            # 案例库（用户数据，每博主一文件 + index.md）
├── references/
│   ├── style-guide.md    # 表达形式规范（生成必读）
│   ├── short-video-copywriting.md # 抖音口播规范（抖音生成必读）
│   ├── frameworks.md     # 选题方向/写作框架库（用户数据）
│   ├── platform-rules.md # 各平台文案规则
│   └── originality.md    # 防洗稿自检清单
├── scripts/
│   ├── douyin_api.py     # 抖音采集（API+cookie，绕过签名bug）
│   ├── transcribe.py     # 口播转写（Whisper + URL刷新）
│   ├── update_library.py # 采集→案例库入库（幂等）
│   ├── similarity.py     # 防洗稿相似度检测
│   ├── collect.py        # 小红书采集（MediaCrawler 包装）
│   ├── setup.sh          # 一键初始化
│   └── run_tests.py      # 离线测试
└── tools/MediaCrawler    # 爬虫引擎（setup.sh 自动 clone）
```

## 测试

```bash
python scripts/run_tests.py
```

## 合规提示

- 仅用于学习研究、个人创作参考；控制采集频率，遵守平台条款。
- 博主内容只做方向与结构参考，不复制文字、不搬运成片。
- 爬虫仅供学习研究（MediaCrawler 许可限制）。
- 生成内容请遵守各平台社区规范与广告法。

## License

MIT（除 tools/MediaCrawler 为其原始许可）
