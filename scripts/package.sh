#!/usr/bin/env bash
# 心语 · 打源码分发包（自动排除敏感与巨型文件）
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION=$(grep -oP 'version="\K[^"]+' "$ROOT/backend/app/main.py")
OUT="$ROOT/dist/xinlyu-v${VERSION}.tar.gz"
mkdir -p "$ROOT/dist"
tar -czf "$OUT" -C "$ROOT" \
  --exclude='.venv' --exclude='__pycache__' --exclude='*.gguf' \
  --exclude='.git' --exclude='dist' --exclude='.pytest_cache' \
  --exclude='.diary_key' --exclude='.pytest_cache' \
  backend static scripts README.md LICENSE
# 发布自检：包里出现敏感文件即刻失败
if tar -tzf "$OUT" | grep -qE "diary_key|\.gguf|diary\.db"; then
  echo "❌ 包内含敏感文件，禁止发布"; rm "$OUT"; exit 1
fi
echo "✅ $OUT"
