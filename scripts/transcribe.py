# -*- coding: utf-8 -*-
"""抖音口播转写：下载视频 → ffmpeg 提取音频 → faster-whisper 转文字。

用法:
  python scripts/transcribe.py --json data/raw/<文件>.json [--model small]

依赖: faster-whisper, ffmpeg (PATH 中可用)
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP_DIR = os.path.join(ROOT, "data", "transcripts")


def ensure_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True)
    except FileNotFoundError:
        sys.exit("未找到 ffmpeg，请先安装并加入 PATH。")


def download(url: str, dest: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    print(f"下载视频: {url[:80]}...")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "video/mp4,video/*;q=0.8,*/*;q=0.5",
    })
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            if resp.status != 200:
                print(f"[download] HTTP {resp.status}")
                return False
            with open(dest, "wb") as f:
                f.write(resp.read())
    except Exception as e:
        print(f"[download] 失败: {e}")
        return False
    return os.path.exists(dest) and os.path.getsize(dest) > 0


def extract_audio(video: str, wav: str):
    subprocess.run(["ffmpeg", "-y", "-i", video, "-ar", "16000", "-ac", "1",
                    "-vn", wav], check=True, capture_output=True)


def transcribe(wav: str, model_size: str) -> str:
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav, language="zh", vad_filter=True)
    return "".join(seg.text for seg in segments).strip()


def refresh_video_url(aweme_id: str) -> str:
    """通过抖音 detail API 刷新视频下载地址（旧签名 URL 会过期）。"""
    import json as _json
    import urllib.request as _ur
    import websocket
    import requests as _req
    # 从 CDP 取 cookie
    info = _req.get("http://127.0.0.1:9222/json/list", timeout=5).json()
    page = next((t for t in info if t.get("type") == "page"), None)
    if not page:
        return ""
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
    ws.send(_json.dumps({"id": 1, "method": "Network.getAllCookies", "params": {}}))
    cookies = []
    while True:
        m = _json.loads(ws.recv())
        if m.get("id") == 1:
            cookies = m.get("result", {}).get("cookies", [])
            break
    ws.close()
    cookie = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
    hdrs = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/151.0.0.0",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json, text/plain, */*",
    }
    params = {
        "device_platform": "webapp", "aid": "6383", "channel": "channel_pc_web",
        "aweme_id": aweme_id,
    }
    try:
        r = _req.get("https://www.douyin.com/aweme/v1/web/aweme/detail/",
                     headers=hdrs, params=params, timeout=15)
        d = r.json()
        if d.get("status_code") != 0:
            return ""
        aw = d.get("aweme_detail") or {}
        play = (aw.get("video") or {}).get("play_addr") or {}
        urls = play.get("url_list") or []
        return urls[0] if urls else ""
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser(description="抖音口播转写")
    ap.add_argument("--json", required=True, help="collect.py 输出的 JSON")
    ap.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium"])
    args = ap.parse_args()

    ensure_ffmpeg()
    os.makedirs(TMP_DIR, exist_ok=True)
    with open(args.json, "r", encoding="utf-8-sig") as f:
        payload = json.load(f)

    done = 0
    for item in payload.get("items", []):
        if item.get("transcript"):
            continue
        vurl = item.get("video_url", "")
        if not vurl:
            continue
        source_id = str(item.get("source_id") or "unknown")
        safe_id = os.path.basename(source_id)
        video = os.path.join(TMP_DIR, safe_id + ".mp4")
        wav = os.path.join(TMP_DIR, safe_id + ".wav")
        try:
            if not download(vurl, video):
                # 旧签名 URL 过期，刷新后重试一次
                print(f"[refresh] 刷新视频地址: {source_id}")
                fresh = refresh_video_url(source_id)
                if fresh and fresh != vurl:
                    item["video_url"] = fresh
                    vurl = fresh
                    if not download(vurl, video):
                        print(f"[skip] 刷新后仍无法下载: {source_id}")
                        continue
                else:
                    print(f"[skip] 无法获取新地址: {source_id}")
                    continue
            extract_audio(video, wav)
            item["transcript"] = transcribe(wav, args.model)
            done += 1
            print(f"[ok] {source_id}: {item['transcript'][:60]}...")
        except Exception as e:
            item["transcript"] = ""
            print(f"[fail] {source_id}: {e}")
        finally:
            for p in (video, wav):
                if os.path.exists(p):
                    os.remove(p)

    with open(args.json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"转写完成: {done}/{len(payload.get('items', []))} 条")


if __name__ == "__main__":
    main()
