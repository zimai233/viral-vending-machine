# -*- coding: utf-8 -*-
"""抖音博主采集 v4 —— 直接调用抖音 API + Chrome 真实 cookie。

参考 MediaCrawler 的 API 方案，但用 CDP 从已登录 Chrome 取 cookie，
绕过 MediaCrawler 的签名 bug。支持分页拉全量 + 时间过滤。

用法:
  python scripts/douyin_api.py [sec_user_id] [count] [months]
"""
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests
import websocket

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")

DEFAULT_SEC = "MS4wLjABAAAA0106vF0XfBGfWm8HVl92Mk8ibA1Mydt4awnbMDut5so"
DEFAULT_AUTHOR = "皇阿玛"


def get_cookie_str():
    """从 CDP 当前页面拿全部 cookie。"""
    info = requests.get("http://127.0.0.1:9222/json/list", timeout=5).json()
    page = next(t for t in info if t.get("type") == "page")
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    ws.send(json.dumps({"id": 1, "method": "Network.getAllCookies", "params": {}}))
    cookies = []
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == 1:
            cookies = m.get("result", {}).get("cookies", [])
            break
    ws.close()
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def headers_with(cookie):
    return {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
    }


def fetch_posts(sec_user_id, cookie, max_count=100):
    """分页拉取创作者全部作品，返回列表（含 desc/点赞/时间/视频链接）。"""
    base = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    hdrs = headers_with(cookie)
    items = []
    max_cursor = ""
    has_more = 1
    guard = 0
    while has_more and len(items) < max_count and guard < 30:
        guard += 1
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "sec_user_id": sec_user_id,
            "count": "18",
            "max_cursor": str(max_cursor),
            "locate_query": "false",
            "publish_video_strategy_type": "2",
        }
        page_ok = False
        for attempt in range(3):
            try:
                r = requests.get(base, headers=hdrs, params=params, timeout=20)
                if r.status_code == 200:
                    d = r.json()
                else:
                    print(f"  page {guard} HTTP {r.status_code}, retry...")
                    time.sleep(3)
                    continue
            except Exception as e:
                print(f"  page {guard} request error: {e}, retry...")
                time.sleep(3)
                continue
            if d.get("status_code") != 0:
                print(f"  page {guard} status_code={d.get('status_code')}, retry...")
                time.sleep(3)
                continue
            page_ok = True
            break
        if not page_ok:
            print(f"  page {guard} failed after retries, stop")
            break
        aweme_list = d.get("aweme_list") or []
        items.extend(aweme_list)
        has_more = d.get("has_more", 0)
        max_cursor = d.get("max_cursor", "")
        print(f"  拉取第{guard}页: +{len(aweme_list)} 条, 累计 {len(items)}, has_more={has_more}")
        time.sleep(2.0)
        if not aweme_list:
            break
    return items


def normalize(item, author):
    """aweme 原始数据 → 统一格式。"""
    stats = item.get("statistics") or {}
    liked = stats.get("digg_count", 0) or 0
    video = item.get("video") or {}
    play_addr = video.get("play_addr") or {}
    url_list = play_addr.get("url_list") or []
    video_url = url_list[0] if url_list else ""
    return {
        "platform": "douyin",
        "source_id": item.get("aweme_id", ""),
        "title": (item.get("desc") or "")[:100],
        "content": item.get("desc", ""),
        "transcript": "",
        "tags": [],
        "author": author,
        "author_id": str((item.get("author") or {}).get("uid", "")),
        "url": f"https://www.douyin.com/video/{item.get('aweme_id', '')}",
        "video_url": video_url,
        "likes": int(liked),
        "publish_time": item.get("create_time", 0),
    }


def main():
    sec = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SEC
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    months = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0

    print("获取 Chrome cookie...")
    cookie = get_cookie_str()
    if not cookie:
        print("ERROR: 未获取到 cookie")
        sys.exit(1)

    print(f"拉取博主作品 (sec_user_id={sec[:30]}...)")
    raw = fetch_posts(sec, cookie, max_count=200)

    # 作者名从真实数据取（不同博主不同）
    author = DEFAULT_AUTHOR
    if raw:
        author = ((raw[0].get("author") or {}).get("nickname") or DEFAULT_AUTHOR)

    now = time.time()
    cutoff = now - months * 30 * 24 * 3600

    items = [normalize(it, author) for it in raw]
    # 按发布时间过滤近 N 个月
    recent = [it for it in items if it["publish_time"] >= cutoff]
    skipped = len(items) - len(recent)
    if len(recent) < count:
        print(f"  警告: 近{months}个月仅 {len(recent)} 条（需 {count}），已全部保留")
    recent.sort(key=lambda x: x["likes"], reverse=True)
    recent = recent[:count]

    os.makedirs(RAW_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.join(RAW_DIR, f"douyin_{ts}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"platform": "douyin", "collected_at": ts,
                   "items": recent}, f, ensure_ascii=False, indent=2)

    print(f"\n共拉取 {len(items)} 条，近{months}个月 {len(recent)} 条（过滤掉 {skipped} 条旧内容），作者: {author}")
    print(f"DONE: {len(recent)} items -> {path}")
    for it in recent[:10]:
        pt = datetime.fromtimestamp(it["publish_time"], tz=timezone.utc).strftime("%Y-%m-%d")
        print(f"  [{it['likes']}赞 {pt}] {it['title'][:45]}")
    return path


if __name__ == "__main__":
    main()
