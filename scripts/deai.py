# -*- coding: utf-8 -*-
"""去 AI 味检测器：识别中文文案中的 AI 写作痕迹，输出评分与改写建议。

用法:
  python scripts/deai.py --file <文案.txt|md>       # 检测单个文件
  python scripts/deai.py --text "文案内容"           # 检测字符串
  python scripts/deai.py --file x.txt --rewrite     # 输出保真改写建议

原理:
  1. 读取 references/deai-rules.md 的识别库（三类规则，命中扣分不同）
  2. 扫描文案统计命中，计算 AI 味评分 (0-100)
  3. 保真合同: 改写前用占位符锁定数字/专名/引用，避免改错事实
  4. 输出命中清单 + 改写建议

评分:
  0-20  自然，可直接用
  20-40 轻度 AI 味，建议微调
  40-60 明显 AI 味，需改写
  60+   重度 AI 味，强烈建议重写
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_FILE = os.path.join(ROOT, "references", "deai-rules.md")

# 规则权重
WEIGHTS = {
    "一": 3.0,   # 模板连接词
    "二": 2.0,   # 空话套话
    "三": 1.0,   # 高频AI词
    "四": 2.0,   # 翻译腔
}

# 保真合同：数字/百分比/价格/专名（改写时必须保留）
PROTECT_RE = re.compile(
    r"(\d+(?:\.\d+)?%|\d+(?:\.\d+)?万|\d+(?:\.\d+)?亿|"
    r"[¥￥]\s*\d+|\d+\s*元|\d+\s*块|\d+\s*岁|"
    r"[A-Za-z][A-Za-z0-9_.-]*|"     # 英文/产品名
    r"\"[^\"]*\"|“[^”]*”|《[^》]*》)"   # 引用/书名
)


def load_rules():
    """从 deai-rules.md 解析识别库。"""
    rules = {"一": [], "二": [], "三": [], "四": []}
    current = None
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                key = line[3:4]
                if key in rules:
                    current = key
                else:
                    current = None
            elif current and line and not line.startswith("#") and not line.startswith("-"):
                rules[current].append(line)
    return rules


def scan(text, rules):
    """统计命中情况，返回 (命中列表, 评分)。

    短词降噪：长度≤2的词（如"最后""此外"）在口语中常为正常用法，
    需重复出现≥2次才计为 AI 痕迹。
    """
    hits = []
    score = 0.0
    total_len = max(len(text), 1)
    for cat, words in rules.items():
        for w in words:
            if not w:
                continue
            count = text.count(w)
            if count == 0:
                continue
            if len(w) <= 2 and count < 2:
                continue
            hits.append((cat, w, count))
            score += WEIGHTS.get(cat, 1.0) * count
    # 归一化到 100：按每千字命中数估算，命中越多分越高
    per_1000 = score / total_len * 1000
    normalized = min(100, per_1000 * 3)
    return hits, round(normalized, 1)


def protect_facts(text):
    """保真合同：提取并保护关键事实（数字/专名/引用）。"""
    protected = []
    def repl(m):
        protected.append(m.group(0))
        return f"{{F{len(protected)-1}}}"
    masked = PROTECT_RE.sub(repl, text)
    return masked, protected


def rating(score):
    if score <= 20:
        return "自然，可直接用"
    if score <= 40:
        return "轻度 AI 味，建议微调"
    if score <= 60:
        return "明显 AI 味，需改写"
    return "重度 AI 味，强烈建议重写"


def rewrite_suggestions(hits):
    """基于命中生成改写建议。"""
    suggestions = []
    for cat, w, count in hits:
        if cat == "一":
            suggestions.append(f"删除模板连接词「{w}」（出现{count}次），直接说内容")
        elif cat == "二":
            suggestions.append(f"替换空话「{w}」为具体描述（什么方式/多少/结果如何）")
        elif cat == "三":
            suggestions.append(f"精简「{w}」，用更口语的表达替代")
        elif cat == "四":
            suggestions.append(f"翻译腔「{w}」改成中文自然语序")
    return suggestions[:10]


def main():
    ap = argparse.ArgumentParser(description="去AI味检测")
    ap.add_argument("--file", help="检测文件(.txt/.md)")
    ap.add_argument("--text", help="检测文本")
    ap.add_argument("--rewrite", action="store_true", help="同时输出保真改写建议")
    args = ap.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8-sig") as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        sys.exit("需提供 --file 或 --text")

    rules = load_rules()
    hits, score = scan(text, rules)
    masked, protected = protect_facts(text)

    print(f"AI 味评分: {score}/100  ({rating(score)})")
    print(f"命中 {len(hits)} 处:")
    for cat, w, count in hits:
        print(f"  [{cat}类] {w} × {count}")

    if args.rewrite:
        print("\n改写建议:")
        for s in rewrite_suggestions(hits):
            print(f"  - {s}")
        if protected:
            print(f"\n保真合同: {len(protected)} 个关键事实已锁定（改写时不可变更）:")
            for i, p in enumerate(protected[:8]):
                print(f"  F{i}: {p}")

    sys.exit(0 if score <= 40 else 1)


if __name__ == "__main__":
    main()
