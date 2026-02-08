#!/bin/bash
# Claude Token Monitor - 一键启动脚本
# 自动创建虚拟环境、安装依赖、启动应用

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQ_FILE="$SCRIPT_DIR/requirements.txt"

# Check Python 3
if command -v python3 &>/dev/null; then
    PYTHON=python3
elif command -v python &>/dev/null; then
    PYTHON=python
else
    echo "❌ 未找到 Python 3，请先安装 Python 3。"
    exit 1
fi

echo "🔧 使用 Python: $($PYTHON --version)"

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 创建虚拟环境..."
    $PYTHON -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Install / update dependencies
echo "📥 安装依赖..."
pip install -q --upgrade pip
pip install -q -r "$REQ_FILE"

# Launch the app
echo "🚀 启动 Claude Token Monitor..."
exec python "$SCRIPT_DIR/main.py"
