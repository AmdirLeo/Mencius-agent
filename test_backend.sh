#!/bin/bash
# 🧪 测试脚本 - 验证后端 API

echo "🧪 孟子智能体 - API 测试"
echo "=========================================="
echo ""

# 后端 URL
BACKEND_URL="http://localhost:8000"

# 1. 测试健康检查
echo "1️⃣  测试健康检查端点..."
echo "   GET $BACKEND_URL/health"
response=$(curl -s "$BACKEND_URL/health")
if echo "$response" | grep -q "ok"; then
    echo "   ✅ 后端正常运行"
    echo "   📊 响应: $response"
else
    echo "   ❌ 后端未响应，请确认后端服务已启动"
    echo "   💥 响应: $response"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ 后端服务检查完成！"
echo ""
echo "💡 下一步："
echo "   前端应该能成功连接后端 API /api/ask"
echo "   尝试在前端提问，看看是否能收到回答"
echo ""
