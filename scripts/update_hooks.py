# -*- coding: utf-8 -*-
"""从案例库自动提取标题与开头钩子，沉淀到 assets/hooks/。

用法:
  python scripts/update_hooks.py              # 全量重建标题库+钩子库

功能:
  1. 扫描 assets/cases/*.md，提取每条案例的标题
  2. 按框架标签（案例行里的"框架:"字段）归档到 headlines.md
  3. 提取每条口播的开头一句（前~30字），人工筛选后进 hooks.md
  （钩子需要判断力，脚本输出候选，人工确认后保留）

依赖: 无
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES_DIR = os.path.join(ROOT, "assets", "cases")
HOOKS_DIR = os.path.join(ROOT, "assets", "hooks")
HEADLINES = os.path.join(HOOKS_DIR, "headlines.md")
HOOKS = os.path.join(HOOKS_DIR, "hooks.md")

# 框架类型 → 标题库章节
FRAMEWORK_SECTIONS = {
    "揭秘": "揭秘式",
    "避坑": "避坑式",
    "清单": "清单式",
    "金句": "金句式",
    "反差": "反差式",
    "观点": "观点式",
}


def parse_cases():
    """解析 cases/*.md → [{title, framework, author, likes, hook}]。"""
    cases = []
    if not os.path.isdir(CASES_DIR):
        return cases
    for fn in sorted(os.listdir(CASES_DIR)):
        if not fn.endswith(".md") or fn == "index.md":
            continue
        author = fn[:-3]
        path = os.path.join(CASES_DIR, fn)
        content = open(path, "r", encoding="utf-8").read()
        # 按 ## 标题分块
        blocks = re.split(r"^## ", content, flags=re.M)
        for b in blocks[1:]:
            lines = b.split("\n")
            title = lines[0].strip()
            meta = " ".join(lines[1:3])
            fw = ""
            likes = 0
            m = re.search(r"框架:\s*([^\s|]+)", meta)
            if m:
                fw = m.group(1)
            m2 = re.search(r"点赞[:：]\s*([\d.]+万|\d+)", meta)
            if m2:
                s = m2.group(1)
                likes = int(float(s.replace("万", "")) * 10000) if "万" in s else int(s)
            # 提取口播首句作钩子候选
            hook = ""
            m3 = re.search(r"口播[:：]\s*([^\n]{5,40})", b)
            if m3:
                hook = m3.group(1).strip()
            cases.append({
                "title": title, "framework": fw, "author": author,
                "likes": likes, "hook": hook,
            })
    return cases


def build_headlines(cases):
    """按框架归档标题。"""
    sections = {v: [] for v in FRAMEWORK_SECTIONS.values()}
    for c in cases:
        sec = FRAMEWORK_SECTIONS.get(c["framework"].split("/")[0], "观点式")
        sections[sec].append(c)
    lines = ["# 标题库（按框架类型归档）", "",
             "> 由 `scripts/update_hooks.py` 从案例库自动提取，生成时按类型检索复用。",
             "> 格式：`- [标题]（来源: 博主名, 点赞）`", ""]
    for sec, items in sections.items():
        lines.append(f"## {sec}")
        lines.append("")
        for c in sorted(items, key=lambda x: x["likes"], reverse=True):
            src = f"来源: {c['author']}, {c['likes']//10000}万赞" if c["likes"] >= 10000 else f"来源: {c['author']}"
            lines.append(f"- [{c['title']}]（{src}）")
        lines.append("")
    return "\n".join(lines)


def build_hook_candidates(cases):
    """提取口播首句作为钩子候选（去重）。"""
    seen = set()
    candidates = []
    for c in cases:
        if c["hook"] and c["hook"] not in seen:
            seen.add(c["hook"])
            candidates.append(c["hook"])
    return candidates


def main():
    cases = parse_cases()
    if not cases:
        print("未找到案例，先对标入库再运行。")
        sys.exit(1)
    os.makedirs(HOOKS_DIR, exist_ok=True)

    with open(HEADLINES, "w", encoding="utf-8") as f:
        f.write(build_headlines(cases))
    print(f"标题库已更新: {len(cases)} 条 → {HEADLINES}")

    candidates = build_hook_candidates(cases)
    print(f"\n钩子候选（{len(candidates)} 条，人工确认后加入 hooks.md）:")
    for i, h in enumerate(candidates[:15]):
        print(f"  {i+1}. {h}")


if __name__ == "__main__":
    main()
