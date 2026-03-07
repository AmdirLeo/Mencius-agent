#!/bin/bash
# 🚀 快速启动脚本 - 孟子智能体开发环境

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "=================================================="
echo "🎯 孟子智能体快速启动"
echo "=================================================="
echo ""

# 检查环境
echo "📋 环境检查..."
if ! command -v conda &> /dev/null; then
    echo "❌ 未找到 conda，请先安装 Miniconda"
    exit 1
fi

if ! conda info --envs | grep -q "men"; then
    echo "❌ 未找到 conda 环境 'men'，请创建: conda create -n men python=3.10"
    exit 1
fi

echo "✅ Conda 环境 'men' 存在"
echo ""

# 激活环境
echo "🔧 配置环境..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate men

# 检查 Python 依赖
echo "📦 检查 Python 依赖..."
if [ ! -d "$ROOT_DIR/backend/venv" ] && ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 安装 Python 依赖..."
    cd "$ROOT_DIR/backend"
    pip install -r requirements.txt -q
    echo "✅ Python 依赖安装完成"
fi

# 检查 Node 依赖
echo "📦 检查 Node.js 依赖..."
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "📥 安装 Node.js 依赖..."
    cd "$ROOT_DIR/frontend"
    npm install -q
    echo "✅ Node.js 依赖安装完成"
fi

# 验证 .env 文件
echo "⚙️  验证配置文件..."
if [ ! -f "$ROOT_DIR/backend/.env" ]; then
    echo "⚠️  复制 .env.example 到 .env..."
    cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
    echo "⚠️  重要：请编辑 backend/.env 文件，填入你的 GLM_API_KEY"
fi

# 显示启动信息
echo ""
echo "=================================================="
echo "✅ 初始化完成！"
echo "=================================================="
echo ""
echo "📌 下一步：在两个不同的终端中运行以下命令"
echo ""
echo "【终端 1】启动后端服务："
echo "  cd $ROOT_DIR"
echo "  conda activate men"
echo "  cd backend"
echo "  python -m uvicorn app.main:app --reload --port 8000"
echo ""
echo "【终端 2】启动前端应用："
echo "  cd $ROOT_DIR/frontend"
echo "  npm run dev"
echo ""
echo "📌 访问应用："
echo "  🌐 http://localhost:5173"
echo ""
echo "📌 后端 API："
echo "  🔌 http://localhost:8000"
echo "  💓 健康检查: http://localhost:8000/health"
echo ""
echo "💡 提示："
echo "  - 需要填入 GLM_API_KEY 才能正常使用"
echo "  - 获取 API Key: https://open.bigmodel.cn/"
echo "  - 向量数据库可选: docker-compose up -d"
echo ""
