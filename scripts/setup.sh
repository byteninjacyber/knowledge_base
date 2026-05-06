#!/bin/bash
set -e

KB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$KB_DIR"

if ! command -v python3 &>/dev/null; then
    echo "请先安装 Python 3"
    exit 1
fi

pip install pyyaml -q 2>/dev/null || pip3 install pyyaml -q 2>/dev/null

if [ ! -f ".env" ]; then
    echo "KB_AI_KEY=sk-or-v1-你的openrouter-key" > .env
    echo "已创建 .env 文件，请填入你的 OpenRouter API Key"
fi

echo "✅ 环境就绪，可以开始使用"
echo ""
echo "常用命令："
echo "  kb new <标题>     创建新笔记"
echo "  kb push           提交并发布"
echo "  kb ai [文件]      AI 整理"
echo "  kb apply          应用 AI 建议"
