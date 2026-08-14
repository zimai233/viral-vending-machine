# -*- coding: utf-8 -*-
"""口播转写后处理：专名修正 + 删气口 + 分段。

用法:
  python scripts/enhance_transcript.py --json <转写后的JSON> [--remove-fillers] [--split]

功能:
  1. 专名修正: 按 assets/glossary.tsv 批量修正 Whisper 误识别（人名/产品名/术语）
  2. 删气口(可选): 删除 "嗯/啊/那个/就是/然后" 等口头禅
  3. 分段(可选): 按句号/问号切分为段落，便于阅读与剪辑

依赖: 无（纯文本处理）
"""
import argparse
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOSSARY = os.path.join(ROOT, "assets", "glossary.tsv")

# 气口/口头禅（删气口时移除，保留语义）
FILLERS = [
    "那个", "就是说", "怎么说呢", "呃", "嗯嗯", "额", "然后那个",
    "其实吧", "怎么说", "你们知道吗", "对吧", "哈", "哎",
]

# 英文标点残留修复
SPACE_FIX = re.compile(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])")


def load_glossary():
    """读取专名词表 → {误写: 正确写法}。"""
    mapping = {}
    if not os.path.exists(GLOSSARY):
        return mapping
    with open(GLOSSARY, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            correct = parts[0].strip()
            wrongs = [w.strip() for w in parts[1].split(",") if w.strip()]
            for w in wrongs:
                if w:
                    mapping[w] = correct
    return mapping


def fix_glossary(text, mapping):
    """专名修正：把误识别替换为正确写法（长词优先，一次性扫描避免重复替换）。"""
    if not mapping:
        return text
    # 长词优先排序
    terms = sorted(mapping, key=len, reverse=True)
    result = []
    i = 0
    while i < len(text):
        matched = False
        for wrong in terms:
            if text.startswith(wrong, i):
                result.append(mapping[wrong])
                i += len(wrong)
                matched = True
                break
        if not matched:
            result.append(text[i])
            i += 1
    return "".join(result)


def remove_fillers(text, fillers=None):
    """删除气口/口头禅。"""
    if fillers is None:
        fillers = FILLERS
    for f in fillers:
        text = text.replace(f, "")
    # 清理多余空格与重复标点
    text = SPACE_FIX.sub(r"\1\2", text)
    text = re.sub(r"[，、]{2,}", "，", text)
    text = re.sub(r"(\s)\1+", r"\1", text)
    return text.strip()


def split_paragraphs(text, max_len=120):
    """按句号/问号/感叹号分段，每段不超过 max_len 字。"""
    sentences = re.split(r"(?<=[。！？!?])", text)
    paragraphs = []
    cur = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(cur) + len(s) <= max_len:
            cur += s
        else:
            if cur:
                paragraphs.append(cur)
            cur = s
    if cur:
        paragraphs.append(cur)
    return "\n".join(paragraphs)


def main():
    ap = argparse.ArgumentParser(description="口播转写后处理")
    ap.add_argument("--json", required=True, help="transcribe.py 输出的 JSON")
    ap.add_argument("--remove-fillers", action="store_true", help="删气口")
    ap.add_argument("--split", action="store_true", help="分段")
    args = ap.parse_args()

    with open(args.json, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)

    mapping = load_glossary()
    fixed = 0
    for item in payload.get("items", []):
        t = item.get("transcript", "")
        if not t:
            continue
        orig = t
        t = fix_glossary(t, mapping)
        if args.remove_fillers:
            t = remove_fillers(t)
        if args.split:
            t = split_paragraphs(t)
        if t != orig:
            item["transcript"] = t
            fixed += 1

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"增强完成: 处理 {fixed}/{len(payload.get('items', []))} 条")
    if mapping:
        print(f"  专名词表: {len(mapping)} 个映射")


if __name__ == "__main__":
    main()
