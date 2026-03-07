#!/bin/bash
# Frontend startup script

cd "$(dirname "$0")"

echo "🚀 Starting Mencius Agent Frontend..."

# 确保位于 frontend 目录
cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# 启动 Vite 开发服务器
npm run dev
