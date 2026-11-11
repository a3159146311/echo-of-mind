#!/usr/bin/env bash
# 心语 · 一键启动：llama-server + FastAPI + 浏览器
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_BIN="${XINLYU_LLAMA:-$HOME/code/projects/llama.cpp/build/bin/llama-server}"
MODEL="${XINLYU_MODEL:-$HOME/code/projects/models/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
PORT_LLM=8080; PORT_API=8000

[ -x "$LLAMA_BIN" ] || { echo "❌ 找不到 llama-server：$LLAMA_BIN（可用 XINLYU_LLAMA 环境变量指定）"; exit 1; }
[ -f "$MODEL" ]     || { echo "❌ 找不到模型：$MODEL（可用 XINLYU_MODEL 指定，或运行 scripts/install.sh）"; exit 1; }

# 清理残留进程，防止端口占用
kill $(lsof -t -i:$PORT_LLM) 2>/dev/null || true
kill $(lsof -t -i:$PORT_API) 2>/dev/null || true

echo "🕯️ 正在拉起本地模型（Qwen2.5-1.5B）……"
"$LLAMA_BIN" -m "$MODEL" -t 4 --port $PORT_LLM > /tmp/xinlyu-llm.log 2>&1 &
LLM_PID=$!
trap 'kill $LLM_PID $API_PID 2>/dev/null' EXIT

echo "🌙 正在拉起心语服务……"
cd "$ROOT/backend" && uv run uvicorn app.main:app --port $PORT_API > /tmp/xinlyu-api.log 2>&1 &
API_PID=$!

# 等服务就绪（最多 20 秒）
for i in $(seq 1 20); do
  curl -sf http://localhost:$PORT_API/api/health > /dev/null && break
  [ $i -eq 20 ] && { echo "❌ 服务未能启动，查看 /tmp/xinlyu-api.log"; exit 1; }
  sleep 1
done

echo "✅ 心语已就绪：http://localhost:$PORT_API （Ctrl+C 全部停止）"
xdg-open http://localhost:$PORT_API 2>/dev/null || open http://localhost:$PORT_API 2>/dev/null || true
wait
