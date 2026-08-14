#!/usr/bin/env bash
# 打包 social-content-studio skill 为可分发的 zip
# 用法: bash scripts/package.sh [version]
# 默认版本从 SKILL.md frontmatter 读取
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 版本号：默认取 SKILL.md 里的 version，可被参数覆盖
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
  VERSION="$(grep -m1 'version:' SKILL.md | sed 's/.*version: *//' | tr -d '"' || echo "0.1.0")"
fi
OUT_DIR="${OUT_DIR:-$ROOT/..}"
OUT_NAME="social-content-studio-v${VERSION}.zip"
OUT_PATH="$OUT_DIR/$OUT_NAME"

# 目标清单（打包内容）
FILES=(
  "SKILL.md"
  "README.md"
  ".gitignore"
  "assets"
  "references"
  "scripts"
  "tools/.gitkeep"
)

echo "== 打包 skill v${VERSION} =="
TMP="$(mktemp -d)"
PKG="$TMP/social-content-studio"
mkdir -p "$PKG"

for f in "${FILES[@]}"; do
  if [ -e "$f" ]; then
    cp -r "$f" "$PKG/"
    echo "  ✓ $f"
  else
    echo "  ✗ 缺失: $f"
    exit 1
  fi
done

# 排除临时/运行时产物
find "$PKG" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$PKG" -name "*.pyc" -delete 2>/dev/null || true

# 打包（兼容 zip / tar / PowerShell Compress-Archive）
rm -f "$OUT_PATH"
if command -v zip >/dev/null 2>&1; then
  (cd "$TMP" && zip -rq "$OUT_PATH" social-content-studio)
elif command -v tar >/dev/null 2>&1 && tar --version 2>&1 | grep -qi bsdtar; then
  (cd "$TMP" && tar -a -cf "$OUT_PATH" social-content-studio)
else
  # PowerShell fallback (Windows)
  powershell.exe -NoProfile -Command "Compress-Archive -Path '$TMP/social-content-studio' -DestinationPath '$OUT_PATH' -Force"
fi
rm -rf "$TMP"

echo ""
echo "✅ 已生成: $OUT_PATH"
echo ""
echo "== 安装到新电脑 =="
echo "1. 解压 zip 到新电脑的 .opencode/skills/ 目录（覆盖/合并 social-content-studio/）"
echo "2. 运行: bash .opencode/skills/social-content-studio/scripts/setup.sh"
echo "   （装依赖 + 克隆 MediaCrawler + Chrome 登录引导）"
echo "3. 开始使用"
