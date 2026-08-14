# -*- coding: utf-8 -*-
"""发布前总检：一键检查文案是否达到发布标准。

用法:
  python scripts/prepublish_check.py --file <文案.txt|md> [--platform xhs|douyin|wechat]
                                      [--refs <原文目录/JSON>] [--title "标题"]

检查项:
  1. AI味评分   (deai.py)     — 超40分警告，超60分失败
  2. 违禁词检测 (compliance.py) — 硬性违禁即失败
  3. 字数/长度  (平台规则)     — 过短或过长警告
  4. 标题检查   (有标题时)     — 标题长度/是否含禁词
  5. 洗稿相似度 (similarity.py) — 传 --refs 时检测

退出码: 0=通过, 1=警告(建议修改), 2=失败(必须修改)
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import deai
import compliance

# 平台字数范围（口播/文案正文字数）
PLATFORM_LEN = {
    "xhs": (50, 1200),
    "douyin": (30, 500),
    "wechat": (300, 5000),
}

LEVEL_EMOJI = {0: "✅ 通过", 1: "⚠️ 警告", 2: "❌ 失败"}


def check_length(text, platform):
    """字数检查。"""
    n = len(text)
    lo, hi = PLATFORM_LEN.get(platform, (30, 1200))
    if n < lo:
        return 1, f"字数不足: {n}字（{platform}建议≥{lo}字）"
    if n > hi:
        return 1, f"字数过长: {n}字（{platform}建议≤{hi}字）"
    return 0, f"字数正常: {n}字"


def check_title(title, words):
    """标题检查。"""
    if not title:
        return 0, "未提供标题（跳过）"
    if len(title) > 30:
        return 1, f"标题过长: {len(title)}字（建议≤30字）"
    for level, wlist in words.items():
        for w in wlist:
            if w and w in title and level == "一":
                return 2, f"标题含硬性违禁词: {w}"
    return 0, f"标题正常: {title[:20]}..."


def main():
    ap = argparse.ArgumentParser(description="发布前总检")
    ap.add_argument("--file", required=True, help="待检文案文件")
    ap.add_argument("--platform", default="douyin", choices=["xhs", "douyin", "wechat"])
    ap.add_argument("--title", default="", help="标题（可选）")
    ap.add_argument("--refs", default="", help="洗稿检测参考（JSON/目录/文本，可选）")
    args = ap.parse_args()

    with open(args.file, "r", encoding="utf-8-sig") as f:
        text = f.read()

    results = []  # (level, label, msg)
    max_level = 0

    # 1. AI 味
    rules = deai.load_rules()
    hits, ai_score = deai.scan(text, rules)
    if ai_score > 60:
        results.append((2, "AI味", f"评分{ai_score}/100 重度AI味，必须改写"))
        max_level = 2
    elif ai_score > 40:
        results.append((1, "AI味", f"评分{ai_score}/100 明显AI味，建议改写"))
        max_level = max(max_level, 1)
    else:
        results.append((0, "AI味", f"评分{ai_score}/100 自然"))

    # 2. 违禁词
    words = compliance.load_words()
    chits, hard = compliance.check(text, words)
    if hard > 0:
        hard_words = "、".join(w for _, w, _, _ in chits if _ == "一")[:40]
        results.append((2, "违禁词", f"含硬性违禁: {hard_words}"))
        max_level = 2
    elif chits:
        wd = "、".join(w for _, w, _, _ in chits if _ != "一")[:40]
        results.append((1, "违禁词", f"含风险词: {wd}"))
        max_level = max(max_level, 1)
    else:
        results.append((0, "违禁词", "无违禁词"))

    # 3. 字数
    lvl, msg = check_length(text, args.platform)
    results.append((lvl, "字数", msg))
    max_level = max(max_level, lvl)

    # 4. 标题
    lvl, msg = check_title(args.title, words)
    results.append((lvl, "标题", msg))
    max_level = max(max_level, lvl)

    # 5. 洗稿（可选）— 只检测正文，排除标题（标题借鉴是正常操作）
    if args.refs:
        import similarity
        body = text
        # 去掉首行（标题通常在第一行）和 --title 前缀
        lines = body.split("\n")
        if len(lines) > 1:
            body = "\n".join(lines[1:])
        elif args.title and body.startswith(args.title):
            body = body[len(args.title):]
        refs = similarity.load_refs(args.refs)
        if refs:
            rows = similarity.report(body, refs)
            max_s = max((s for _, s, _, _ in rows), default=0)
            has_run = any(run for _, _, run, _ in rows)
            if max_s > 0.30 or has_run:
                results.append((1, "洗稿", f"最高相似度{max_s:.2f}或连续命中，需改写"))
                max_level = max(max_level, 1)
            else:
                results.append((0, "洗稿", f"最高相似度{max_s:.2f}，安全"))

    # 输出
    print(f"=== 发布前检查 [{args.platform}] ===")
    print(f"文件: {args.file}")
    print()
    for lvl, label, msg in results:
        print(f"  {LEVEL_EMOJI[lvl]} [{label}] {msg}")
    print()
    print(f"结论: {LEVEL_EMOJI[max_level]}")
    sys.exit(max_level)


if __name__ == "__main__":
    main()
