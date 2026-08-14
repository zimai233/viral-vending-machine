# -*- coding: utf-8 -*-
"""包装 MediaCrawler 的采集脚本。

用法:
  python collect.py --platform xhs --mode creator --target <主页链接或ID> --count 10
  python collect.py --platform dy  --mode search  --target "AI工具" --count 10

流程:
  1. 解析输入 → 构造 MediaCrawler 命令行参数
  2. 在 tools/MediaCrawler 下执行 uv run main.py
  3. 读取 data/<platform>/json/ 下最新 JSON → 归一化为统一格式
  4. 按互动量倒序裁剪到 count 条 → 写 data/raw/<时间戳>.json
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MC_DIR = os.path.join(ROOT, "tools", "MediaCrawler")
RAW_DIR = os.path.join(ROOT, "data", "raw")

PLATFORM_ALIAS = {"xiaohongshu": "xhs", "xhs": "xhs", "小红书": "xhs",
                  "douyin": "dy", "dy": "dy", "抖音": "dy"}

CREATOR_RE = {
    "xhs": r"/user/profile/([0-9a-zA-Z]+)",
    "dy": r"/user/([0-9a-zA-Z_-]+)",
}
NOTE_ID_RE = {
    "xhs": r"/explore/([0-9a-zA-Z]+)",
    "dy": r"/video/(\d+)",
}


def detect_platform(target: str) -> str:
    """从 URL 或别名推断平台代码。"""
    lower = target.lower()
    if "xiaohongshu.com" in lower or "/explore/" in lower:
        return "xhs"
    if "douyin.com" in lower or "/video/" in lower:
        return "dy"
    return ""


def extract_creator_id(platform: str, url: str) -> str:
    m = re.search(CREATOR_RE[platform], url)
    if not m:
        raise ValueError(f"无法从 URL 提取创作者ID: {url}")
    return m.group(1)


def extract_note_id(platform: str, url: str) -> str:
    m = re.search(NOTE_ID_RE["xhs" if platform == "xhs" else "dy"], url)
    if not m:
        raise ValueError(f"无法从 URL 提取内容ID: {url}")
    return m.group(1)


def extract_aweme_id(platform: str, url: str) -> str:
    m = re.search(NOTE_ID_RE["dy"], url)
    if not m:
        raise ValueError(f"无法从 URL 提取视频ID: {url}")
    return m.group(1)


def build_mc_args(platform: str, mode: str, target: str, count: int) -> list:
    """构造 MediaCrawler main.py 参数。"""
    args = ["uv", "run", "main.py",
            "--platform", platform,
            "--lt", "qrcode",
            "--save_data_option", "json",
            "--crawler_max_notes_count", str(count),
            "--headless", "no",
            "--get_comment", "no"]
    if mode == "creator":
        args += ["--type", "creator", "--creator_id", target]
    else:
        args += ["--type", "search", "--keywords", target]
    return args


def run_mediacrawler(platform: str, mode: str, target: str, count: int) -> list:
    """在 tools/MediaCrawler 下执行爬虫，返回归一化列表。"""
    if not os.path.isdir(MC_DIR):
        raise RuntimeError(
            "未找到 tools/MediaCrawler。请先运行 scripts/setup.sh 完成初始化。")
    args = build_mc_args(platform, mode, target, count)
    print(f"运行: {' '.join(args)} (cwd={MC_DIR})")
    proc = subprocess.run(args, cwd=MC_DIR)
    if proc.returncode != 0:
        raise RuntimeError("MediaCrawler 执行失败，请检查登录态/网络。")
    return read_latest_json(platform)


def read_latest_json(platform: str) -> list:
    """读取 MediaCrawler 输出目录最新的内容 JSON。

    MediaCrawler 文件名格式: {crawler_type}_{item_type}_{date}.json
    item_type 在 store 中固定为 "contents"，如 search_contents_20260813.json。
    优先匹配 *_contents_*.json，兜底取任意 .json。
    """
    json_dir = os.path.join(MC_DIR, "data", platform, "json")
    contents = [f for f in glob.glob(os.path.join(json_dir, "*_contents_*.json"))
                if os.path.isfile(f)]
    fallback = [f for f in glob.glob(os.path.join(json_dir, "*.json"))
                if os.path.isfile(f)]
    candidates = contents or fallback
    if not candidates:
        raise RuntimeError(f"未找到采集结果 JSON ({json_dir})")
    latest = max(candidates, key=os.path.getmtime)
    with open(latest, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def _extract_tags(raw) -> list:
    """兼容 tag_list 的两种形态：逗号字符串 或 dict 列表。"""
    if isinstance(raw, list):
        return [t.get("name", "") if isinstance(t, dict) else str(t)
                for t in raw if t]
    return [t for t in (raw or "").split(",") if t]


def _to_int(value) -> int:
    """安全转整数：容忍 None/空/"1,234"/"1.2万"。"""
    if value is None:
        return 0
    s = str(value).replace(",", "").strip()
    if not s:
        return 0
    m = re.match(r"^(\d+)(\.\d+)?", s)
    if not m:
        return 0
    n = float(m.group(0))
    if "万" in s:
        n *= 10000
    return int(n)


def normalize(platform: str, items: list, source_target: str) -> list:
    """MediaCrawler 原始记录 → 统一格式。"""
    out = []
    for it in items:
        if platform == "xhs":
            rec = {
                "platform": "xiaohongshu",
                "source_id": it.get("note_id", ""),
                "title": it.get("title", ""),
                "content": it.get("desc", ""),
                "transcript": "",
                "tags": _extract_tags(it.get("tag_list")),
                "author": it.get("nickname", ""),
                "author_id": it.get("creator_hash", ""),
                "url": it.get("note_url", ""),
                "likes": _to_int(it.get("liked_count")),
                "publish_time": it.get("time", 0),
            }
        else:  # douyin
            rec = {
                "platform": "douyin",
                "source_id": it.get("aweme_id", ""),
                "title": it.get("title", ""),
                "content": it.get("desc", ""),
                "transcript": "",
                "tags": [],
                "author": it.get("nickname", ""),
                "author_id": it.get("creator_hash", ""),
                "url": it.get("aweme_url", ""),
                "video_url": it.get("video_download_url", ""),
                "likes": _to_int(it.get("liked_count")),
                "publish_time": it.get("create_time", 0),
            }
        if rec["source_id"]:
            out.append(rec)
    out.sort(key=lambda r: r["likes"], reverse=True)
    return out


def save_raw(items: list, platform: str) -> str:
    os.makedirs(RAW_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(RAW_DIR, f"{platform}_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"platform": platform, "collected_at": ts,
                   "items": items}, f, ensure_ascii=False, indent=2)
    return path


def main():
    ap = argparse.ArgumentParser(description="自媒体内容采集 (包装 MediaCrawler)")
    ap.add_argument("--platform", required=True, choices=["xhs", "dy", "xiaohongshu", "douyin"])
    ap.add_argument("--mode", required=True, choices=["creator", "search"])
    ap.add_argument("--target", required=True, help="账号链接/ID 或搜索关键词")
    ap.add_argument("--count", type=int, default=10)
    args = ap.parse_args()

    platform = PLATFORM_ALIAS.get(args.platform, args.platform)
    if platform not in ("xhs", "dy"):
        sys.exit("仅支持小红书(xhs)/抖音(dy)")

    target = args.target
    if args.mode == "creator" and "http" in target:
        inferred = detect_platform(target)
        if inferred and inferred != platform:
            platform = inferred
        if platform == "xhs":
            target = extract_creator_id("xhs", target)
        else:
            target = extract_creator_id("dy", target)
    if args.mode == "creator":
        print(f"对标创作者: {target} (平台={platform})")

    raw = run_mediacrawler(platform, args.mode, target, args.count)
    normalized = normalize(platform, raw, target)
    path = save_raw(normalized, platform)
    print(f"采集完成: {len(normalized)} 条 → {path}")
    return path


if __name__ == "__main__":
    main()
