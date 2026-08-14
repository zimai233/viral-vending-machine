# -*- coding: utf-8 -*-
"""违禁词/合规检测器。

用法:
  python scripts/compliance.py --file <文案.txt|md>    # 检测文件
  python scripts/compliance.py --text "文案内容"        # 检测字符串

分级:
  🔴 硬性违禁 — 必须改写（命中即失败）
  🟡 高风险   — 建议改写（命中警告）
  🟢 擦边     — 建议规避（命中提示）

词库文件: references/banned-words.md（可自行增删）
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORDS_FILE = os.path.join(ROOT, "references", "banned-words.md")

LEVELS = {"一": "🔴硬性", "二": "🟡高风险", "三": "🟢擦边"}
# 短词（如"最""第一"）容易误伤，需要更长上下文才报
MIN_LEN_WARN = {"一": 1, "二": 2, "三": 3}


def load_words():
    """解析 banned-words.md → {level: [words]}。"""
    words = {"一": [], "二": [], "三": []}
    current = None
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                key = line[3:4]
                if key in words:
                    current = key
                else:
                    current = None
            elif current and line and not line.startswith("#"):
                words[current].append(line)
    return words


def check(text, words):
    """扫描文本，返回 (命中列表, 硬性违禁数)。

    擦边区（三）的短词（≤2字）需重复出现≥3次才报，避免正常表达误报。
    """
    hits = []
    hard = 0
    for level, wlist in words.items():
        for w in wlist:
            if not w:
                continue
            count = text.count(w)
            if count == 0:
                continue
            # 擦边短词降噪：出现次数太少不报
            if level == "三" and len(w) <= 2 and count < 3:
                continue
            hits.append((level, w, LEVELS[level], count))
            if level == "一":
                hard += 1
    return hits, hard


def main():
    ap = argparse.ArgumentParser(description="违禁词检测")
    ap.add_argument("--file", help="检测文件")
    ap.add_argument("--text", help="检测文本")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8-sig") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        sys.exit("需提供 --file 或 --text")

    words = load_words()
    hits, hard = check(text, words)

    if not hits:
        print("✅ 无违禁词命中")
        sys.exit(0)

    print(f"命中 {len(hits)} 处（硬性违禁 {hard} 个）:")
    for level, w, label, count in hits:
        print(f"  {label} {w} ×{count}")

    if hard > 0:
        print("\n❌ 含硬性违禁词，必须改写后才能发布")
        sys.exit(2)
    print("\n⚠️ 有风险词，建议改写后发布")
    sys.exit(1)


if __name__ == "__main__":
    main()
