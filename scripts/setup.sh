#!/usr/bin/env bash
# 一键初始化 social-content-studio
# 用法: bash scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MC_DIR="$ROOT/tools/MediaCrawler"

echo "== 1/5 检查基础依赖 =="
for cmd in python uv git ffmpeg; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✓ $cmd: $($cmd --version 2>&1 | head -1)"
  else
    echo "  ✗ 缺少 $cmd，请先安装（python>=3.11, uv, git, ffmpeg）"
    exit 1
  fi
done

echo "== 2/5 获取 MediaCrawler =="
if [ ! -d "$MC_DIR/.git" ]; then
  mkdir -p "$ROOT/tools"
  git clone --depth 1 https://github.com/NanmiCoder/MediaCrawler.git "$MC_DIR"
  echo "  ✓ 已 clone MediaCrawler"
else
  echo "  ✓ MediaCrawler 已存在，跳过"
fi

echo "== 3/5 安装 MediaCrawler 依赖 =="
(cd "$MC_DIR" && uv sync)
echo "  ✓ uv sync 完成"

echo "== 4/5 安装转写依赖 =="
uv pip install faster-whisper jieba
echo "  ✓ faster-whisper + jieba 已安装"

echo "== 5/5 登录与验证 =="
cat <<'EOF'
请在 Chrome 中完成以下步骤（一次性）：
1. 打开 chrome://inspect/#remote-debugging，勾选 "Allow remote debugging for this browser instance"
2. 确认页面显示 Server running at: 127.0.0.1:9222
3. 在浏览器中登录小红书/抖音
4. 之后每次采集时，运行爬虫时浏览器会弹出确认框，点击"接受"即可

验证采集是否可用：
  cd .opencode/skills/social-content-studio
  python scripts/collect.py --platform xhs --mode search --target "测试" --count 1
EOF
echo "完成。"
