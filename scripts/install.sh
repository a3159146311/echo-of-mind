#!/usr/bin/env bash
# 心语 · 一键安装：Python 依赖 + 情绪模型
set -euo pipefail

echo "📦 [1/3] 检查 uv……"
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

echo "📚 [2/3] 安装 Python 依赖……"
cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && uv sync

echo "🧠 [3/3] 下载情绪模型（约 1.1GB，国内走 hf-mirror 镜像）……"
mkdir -p "$HOME/code/projects/models"
cd "$HOME/code/projects/models"
if [ ! -f qwen2.5-1.5b-instruct-q4_k_m.gguf ]; then
  curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf \
    "https://hf-mirror.com/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4-k-m.gguf"
fi

echo "⚠️  还差一步：llama.cpp 引擎。两条路任选："
echo "   A) 包管理器安装后设置环境变量：export XINLYU_LLAMA=$(which llama-server)"
echo "   B) 从源码编译：git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp && cmake -B build && cmake --build build -j"
echo "✅ 安装完成。之后运行 scripts/start.sh 即可使用心语。"
