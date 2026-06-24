# 🚀 快速开始 - Mencius Agent

> 一键启动孟子智能体，开始与孟子聊天

---

## ⚡ 最快启动（3 步）

### 1️⃣ 配置 API Key

```bash
# 编辑 .env 文件
nano backend/.env

# 找到这一行，替换为你的 GLM_API_KEY
GLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
```

💡 从 [智谱 AI 开放平台](https://open.bigmodel.cn/) 获取免费试用密钥

### 2️⃣ 启动后端 (终端1)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

看到这条消息说明成功 ✅：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 3️⃣ 启动前端 (终端2)

```bash
cd frontend
npm install
npm run dev
```

看到这条消息说明成功 ✅：
```
VITE v5.0.8 ready in 439 ms
Local:   http://localhost:5173/
```

### 4️⃣ 打开浏览器

访问 **http://localhost:5173** 开始聊天！

---

## 🧪 测试系统

### 测试后端 API

```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "什么是仁义？"}'
```

预期回答：孟子用现代白话文讨论仁义 ✅

### 查看系统状态

```bash
curl http://localhost:8000/api/status
```

预期输出：
```json
{
  "status": "ready",
  "collection": {
    "vectors_count": 148,
    "backend": "FAISS (In-Memory)"
  }
}
```

---

## 🎯 常见问题

### Q: API Key 配额不足怎么办？

**A:** 系统有智能回退机制！
- 如果 GLM API 失败，会自动返回孟子原文段落
- 用户仍能获得回答，不会卡住

### Q: 第一次启动很慢？

**A:** 正常！后端首次启动会：
- 下载向量化模型 (~200MB)
- 加载孟子译注 txt 文件
- 生成向量索引 (FAISS in-memory)

**耗时**: 约 30-60 秒（仅首次）

### Q: 前端无法连接后端？

**检查清单**：
- [ ] 后端运行在 `http://localhost:8000`
- [ ] 前端配置中的 API 地址正确
- [ ] 防火墙没有阻止 8000 端口
- [ ] 两个应用都已成功启动

运行：
```bash
# 测试后端连通性
curl http://localhost:8000/health

# 预期输出
# {"status":"ok","version":"0.1.0"}
```

---

## 📊 系统架构速览

```
你的问题
  ↓
[前端] ChatInterface 组件
  ↓ POST /api/ask
[后端] RAG 检索 → 从 148 个孟子段落中查找相关内容
  ↓
[后端] LLM 生成 → 调用 GLM-4-Flash，生成孟子风格回答
  ↓
[后端] 智能回退 ← 如果 API 失败，返回原文
  ↓
[前端] 显示孟子的回答
```

---

## 🔧 高级配置

### 修改孟子原文路径

如果你的孟子译注文件位置不同：

编辑 `/backend/app/api/routes.py`：

```python
mencius_file = os.path.join(os.path.dirname(__file__), "../../..", "path/to/your/mencius.txt")
```

### 调整向量相似度

在 `/backend/app/api/routes.py` 中修改：

```python
context_docs = await retriever.retrieve(request.question, top_k=5)  # 默认3，改为5
```

### 自定义孟子风格

编辑 `/backend/app/llm/client.py` 中的 `MENCIUS_SYSTEM_PROMPT`

---

## 📈 性能指标

| 指标         | 值            |
| ------------ | ------------- |
| 平均响应时间 | 2-5 秒        |
| 向量库大小   | ~400MB (内存) |
| 并发支持     | ≥10 用户      |
| 向量检索速度 | <100ms        |

---

## 🐛 调试日志

查看后端详细日志：

```bash
# 打开后端终端，直接看输出

# 例如：
# INFO:     127.0.0.1:55606 - "POST /api/ask HTTP/1.1" 200 OK
# Calling GLM-4-Flash with question: 什么是仁义？...
# Generated response (523 chars)
```

---

## 🌐 部署到线上

简单部署方案（Docker）：

```bash
cd backend
docker build -t mencius-agent .
docker run -p 8000:8000 -e GLM_API_KEY=sk-xxx mencius-agent
```

详见 [README.md](./README.md) 的部署章节

---

## ✅ 验证清单

启动完成后，确认：

- [ ] 后端 log: "Application startup complete"
- [ ] 前端 log: "Local:   http://localhost:5173/"
- [ ] 浏览器能打开 http://localhost:5173
- [ ] 可以输入问题并获得回答
- [ ] 系统状态显示 148 个向量

---

**现在就开始与孟子聊天吧！** 🎭

有问题？查看 [README.md](./README.md) 或提交 Issue

