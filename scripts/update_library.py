# -*- coding: utf-8 -*-
"""采集 JSON → 案例库 Markdown。

用法:
  python scripts/update_library.py --json data/raw/<文件>.json [--framework 恋爱关系]

行为:
  1. 为每个作者生成/更新 assets/cases/<作者>.md（完整案例，含口播）
  2. 更新 assets/cases/index.md（博主索引）
  3. 每个案例带框架标签（用于生成时快速定位）

注意:
  - 文件按 source_id 幂等去重，重复采集不会重复写入。
  - 新博主 = 自动新增 cases/<作者>.md；更新旧博主 = 重写该文件。
"""
import argparse
import json
import os
import re
import unicodedata
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = os.path.join(ROOT, "assets", "cases")
INDEX = os.path.join(CASES, "index.md")


def _index_path():
    return os.path.join(CASES, "index.md")


def sanitize(name: str) -> str:
    """文件名安全化：替换非法字符。"""
    name = unicodedata.normalize("NFKC", name)
    return re.sub(r'[\\/:*?"<>|\s]+', "_", name).strip("._")


def _to_int(value) -> int:
    """安全转整数：容忍 None/空/带逗号/中文单位。"""
    if value is None:
        return 0
    s = str(value).replace(",", "").strip()
    m = re.match(r"^(\d+)(\.\d+)?", s)
    if not m:
        return 0
    return int(float(m.group(0)))


def human_likes(n: int) -> str:
    if n >= 10000:
        return f"{n/10000:.1f}万"
    return f"{n:,}"


def _item_date(item: dict) -> str:
    """优先用发布时间，缺失时退回处理日期。"""
    ts = item.get("publish_time")
    if ts:
        try:
            return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            pass
    return datetime.now().strftime("%Y-%m-%d")


def framework_tags(item: dict) -> str:
    """根据标题推断写作框架标签（用于生成时快速定位）。"""
    t = item.get("title", "")
    tags = []
    if "秘密" in t or "不会告诉" in t:
        tags.append("揭秘")
    if "什么样" in t or "哪些" in t or "怎么" in t or "如何" in t:
        tags.append("清单")
    if "不要" in t or "不能" in t or "绝对" in t:
        tags.append("避坑")
    if "觉得" in t or "正常" in t or "反差" in t:
        tags.append("反差")
    if "爱" in t or "幸福" in t or "情" in t:
        tags.append("金句")
    if not tags:
        tags.append("观点")
    return "/".join(tags)


def build_case_md(item: dict) -> str:
    sid = item.get("source_id") or item.get("url") or ""
    marker = f"<!-- id: {sid} -->" if sid else ""
    title = item.get("title") or "(无标题)"
    likes = human_likes(_to_int(item.get("likes")))
    date = _item_date(item)
    url = item.get("url", "")
    framework = framework_tags(item)
    lines = [f"## {title}",
             f"- 点赞: {likes} | 时间: {date} | 框架: {framework}",
             f"- 链接: {url}"]
    if item.get("transcript"):
        lines.append(f"- 口播: {item['transcript']}")
    if item.get("content") and item.get("content") != title:
        lines.append(f"- 简介: {item['content']}")
    lines.append(f"- {marker}")
    lines.append("")
    return "\n".join(lines)


def _build_author_md(author: str, items: list, framework_hint: str) -> str:
    """生成博主完整案例文件内容。"""
    lines = [f"# {author} 案例库", ""]
    lines.append(f"- 来源: 抖音 | 赛道: {framework_hint or '未分类'} | "
                 f"更新: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"- 案例数: {len(items)}")
    lines.append("")
    for it in items:
        lines.append(build_case_md(it))
    return "\n".join(lines)


def _update_index(author: str, framework: str, count: int):
    """更新 cases/index.md 的博主表格。"""
    index_path = _index_path()
    os.makedirs(CASES, exist_ok=True)
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("# 案例库索引\n\n"
                    "> 对标博主清单。每新增一个博主，由 `scripts/update_library.py` 自动维护。\n"
                    "> 每个博主的完整案例见对应文件：`cases/<博主名>.md`\n\n"
                    "## 对标博主\n\n"
                    "| 平台 | 博主 | 赛道 | 案例数 | 最近更新 |\n"
                    "|---|---|---|---|---|\n")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    row = (f"| douyin | {author} | {framework} | {count} | "
           f"{datetime.now().strftime('%Y-%m-%d')} |")
    # 已有该博主行则替换，否则追加
    if f"| {author} |" in content:
        content = re.sub(rf"\| [^|]* \| {re.escape(author)} \|[^\n]*", row, content)
    else:
        content = content.rstrip() + "\n" + row + "\n"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)


def update(payload: dict, framework_hint: str):
    items = payload.get("items", [])
    if not items:
        print("空数据，无更新。")
        return
    # 按作者分组
    by_author = {}
    for it in items:
        author = it.get("author") or "未知作者"
        by_author.setdefault(author, []).append(it)
    for author, author_items in by_author.items():
        # 幂等：只保留尚未入库的（source_id 去重）
        safe = sanitize(author)
        file_path = os.path.join(CASES, f"{safe}.md")
        existing_ids = set()
        if os.path.exists(file_path):
            content = open(file_path, "r", encoding="utf-8").read()
            existing_ids = set(re.findall(r"<!-- id: (\S+) -->", content))
        fresh = [it for it in author_items
                 if (it.get("source_id") or it.get("url")) not in existing_ids]
        if not fresh:
            print(f"跳过 {author}: {len(author_items)} 条已存在")
            continue
        os.makedirs(CASES, exist_ok=True)
        all_items = fresh if not os.path.exists(file_path) else _merge_existing(file_path, fresh)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(_build_author_md(author, all_items, framework_hint))
        _update_index(author, framework_hint, len(all_items))
        print(f"更新 {author}: 新增 {len(fresh)} 条，共 {len(all_items)} 条 → {file_path}")


def _merge_existing(file_path: str, fresh: list) -> list:
    """合并旧文件已有案例与新案例（按 source_id 去重）。"""
    content = open(file_path, "r", encoding="utf-8").read()
    # 按 <!-- id: xxx --> 分块解析
    parts = re.split(r"<!-- id: (\S+) -->", content)
    # parts[0] 是头部，之后每两项 (id, body) 为一案例
    existing = []
    for i in range(1, len(parts) - 1, 2):
        sid, body = parts[i], parts[i + 1]
        item = {"source_id": sid, "url": "", "title": "", "likes": 0,
                "publish_time": 0, "content": "", "transcript": ""}
        for ln in body.split("\n"):
            if ln.startswith("## "):
                item["title"] = ln[3:].strip()
            elif ln.startswith("- 点赞:"):
                m = re.search(r"([\d.]+)(万)?", ln)
                if m:
                    n = float(m.group(1))
                    item["likes"] = int(n * 10000) if m.group(2) else int(n)
            elif ln.startswith("- 口播:"):
                item["transcript"] = ln[5:].strip()
            elif ln.startswith("- 链接:"):
                item["url"] = ln[6:].strip()
        existing.append(item)
    seen = {it["source_id"] for it in existing}
    for it in fresh:
        if it.get("source_id") not in seen:
            existing.append(it)
    return existing


def main():
    ap = argparse.ArgumentParser(description="采集JSON → 案例库")
    ap.add_argument("--json", required=True)
    ap.add_argument("--framework", default="", help="博主赛道/框架标签，如 恋爱关系")
    args = ap.parse_args()
    with open(args.json, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    update(payload, args.framework)


if __name__ == "__main__":
    main()
