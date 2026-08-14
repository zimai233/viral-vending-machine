# -*- coding: utf-8 -*-
"""n-gram 相似度检测，用于防洗稿把关。

用法:
  python scripts/similarity.py --draft <生成文案.txt> --refs <原文.json 或 目录>
  python scripts/similarity.py --draft a.txt --refs b.txt
"""
import argparse
import json
import os
import re
import sys

PUNCT_RE = re.compile(r"[\s，。！？、；：,.!?;:()（）\"'“”…\-—_/\\#@]+")


def clean(text: str) -> str:
    return PUNCT_RE.sub("", text)


def ngrams(text: str, n: int = 2):
    s = clean(text)
    if len(s) < n:
        return {s} if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    ga, gb = ngrams(a, 2), ngrams(b, 2)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga | gb)


def has_six_char_run(a: str, b: str) -> bool:
    """检测是否出现连续 6+ 字相同片段。"""
    sa, sb = clean(a), clean(b)
    for i in range(len(sa) - 5):
        if sa[i:i + 6] in sb:
            return True
    return False


def load_refs(path: str):
    """读取引用文本列表：JSON(采集格式)/目录(递归)/单个文本。"""
    texts = []
    if os.path.isdir(path):
        for fn in os.listdir(path):
            fp = os.path.join(path, fn)
            if os.path.isdir(fp):
                texts.extend(load_refs(fp))
            elif fn.lower().endswith((".json", ".txt", ".md")):
                texts.extend(load_refs(fp))
        return texts
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8-sig") as f:
            payload = json.load(f)
        items = payload.get("items", payload if isinstance(payload, list) else [])
        for it in items:
            body = it.get("content") or it.get("transcript") or ""
            if body:
                texts.append((it.get("source_id", "?"), body))
        return texts
    with open(path, "r", encoding="utf-8-sig") as f:
        return [("ref", f.read())]


def report(draft: str, refs) -> list:
    rows = []
    for name, ref in refs:
        s = similarity(draft, ref)
        run = has_six_char_run(draft, ref)
        rows.append((name, s, run, ref))
    return rows


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="洗稿相似度检测")
    ap.add_argument("--draft", required=True, help="生成的文案文件(.txt/.md)")
    ap.add_argument("--refs", required=True, help="原文JSON/目录/文本")
    ap.add_argument("--threshold", type=float, default=0.30)
    args = ap.parse_args()

    with open(args.draft, "r", encoding="utf-8-sig") as f:
        draft = f.read()
    refs = load_refs(args.refs)
    rows = report(draft, refs)

    if not rows:
        print("无参考文本可对比。")
        sys.exit(2)

    max_s = 0.0
    flagged = False
    for name, s, run, _ in rows:
        mark = "⚠️" if s > args.threshold or run else "✅"
        if s > args.threshold or run:
            flagged = True
        max_s = max(max_s, s)
        print(f"{mark} [{name}] 相似度={s:.2f} 连续命中={'是' if run else '否'}")
        if s > args.threshold:
            print(f"   → 超过阈值 {args.threshold}，需改写")

    print(f"\n最高相似度: {max_s:.2f} | 结论: {'存在洗稿风险' if flagged else '通过'}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
