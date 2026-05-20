#!/bin/bash
# Backend startup script

cd "$(dirname "$0")"

echo "🚀 Starting Mencius Agent Backend..."
echo "Environment: men"

# 启动 FastAPI 开发服务器
python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
