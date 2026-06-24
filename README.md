# 孟子智能体 - Mencius Agent

> 一个在线聊天应用。通过 RAG + LLM 技术，像孟子那样用白话文和你讨论人生哲学。

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/python-3.10-blue) ![Vue](https://img.shields.io/badge/vue-3-green) ![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🎯 核心特性

- **孟子对话** - 用现代白话文，而不是古文。像个微信里的长辈那样聊天
- **辩论启蒙** - 用反问、类比引导你思考，而不是直接命令
- **知识检索** - 从孟子译注中自动检索相关内容，不会瞎编
- **智能回退** - GLM API 不可用时，直接返回相关孟子段落（不会卡住）
- **简洁架构** - 内存向量库 (FAISS)，无需额外数据库服务

---

## 🚀 快速开始

### 1. 环境准备

**克隆项目**
```bash
git clone https://github.com/yourusername/Mencius-agent.git
cd Mencius-agent
```

**配置 GLM API Key**
```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的 GLM_API_KEY
```

从 [智谱 AI 开放平台](https://open.bigmodel.cn/) 获取 API Key（支持免费试用额度）

### 2. 启动服务

**后端** (终端 1)
```bash
conda activate men
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**前端** (终端 2)
```bash
cd frontend
npm install
npm run dev
```

### 3. 打开浏览器

访问 **http://localhost:5173** 开始与孟子对话

---

## 📊 系统架构

```
┌─────────────────────────────────────────┐
│    Vue 3 前端 (localhost:5173)          │
│  ┌───────────────────────────────────┐  │
│  │    ChatInterface 组件             │  │
│  │  (消息展示 + 输入框)              │  │
│  └───┬───────────────────────────────┘  │
└──────┼──────────────────────────────────┘
       │ POST /api/ask
       ▼
┌─────────────────────────────────────────┐
│    FastAPI 后端 (localhost:8000)        │
│  ┌───────────────────────────────────┐  │
│  │ 1️⃣ RAG 检索 (FAISS)              │  │
│  │    ↓ 从孟子译注中查找相关段落    │  │
│  │ 2️⃣ Prompt 组装                   │  │
│  │    ↓ 系统提示 + 用户问题 + 上下文 │  │
│  │ 3️⃣ LLM 调用 (GLM-4-Flash)       │  │
│  │    ↓ 生成孟子风格回答             │  │
│  │ 4️⃣ 回退机制                      │  │
│  │    ↓ API失败时返回原文            │  │
│  └───┬─────────────────────────────┘  │
└──────┼──────────────────────────────────┘
       │ 返回 JSON 响应
       ▼
    前端展示回答
```

---

## 📁 项目结构

```
Mencius-agent/
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # API 端点 (/api/ask, /api/status, etc)
│   │   ├── llm/client.py          # GLM-4-Flash API 集成
│   │   ├── rag/retriever.py       # FAISS 向量检索
│   │   ├── data/
│   │   │   ├── loader.py          # 加载孟子译注.txt
│   │   │   ├── chunker.py         # 文本分段
│   │   │   └── embedder.py        # 文本向量化
│   │   ├── config/settings.py     # 环境变量配置
│   │   └── main.py                # FastAPI 应用入口
│   ├── requirements.txt           # Python 依赖
│   └── .env.example               # 环境变量示例
├── frontend/
│   ├── src/
│   │   ├── components/ChatInterface.vue
│   │   ├── services/api.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
├── data/raw/孟子译注.txt          # 孟子数据源
└── README.md
```

---

## 🔌 API 说明

### POST `/api/ask` - 提问孟子

**请求**
```json
{
  "question": "什么是仁义？",
  "top_k": 3
}
```

| 字段     | 类型    | 说明                    |
| -------- | ------- | ----------------------- |
| question | string  | 用户问题（必需）        |
| top_k    | integer | 检索相关段落数（默认3） |

**响应 - 成功**
```json
{
  "answer": "仁义啊，这是...",
  "sources": [
    {
      "text": "孟子说：君之视臣...",
      "score": 0.85,
      "metadata": { "section": "尽心下" }
    }
  ],
  "status": "success"
}
```

**响应 - 回退模式**（GLM API 不可用）
```json
{
  "answer": "孟子曰：\n其一：...\n其二：...",
  "sources": [...],
  "status": "fallback_rag_only"
}
```

| 状态                | 说明                 |
| ------------------- | -------------------- |
| `success`           | 正常，使用 LLM 生成  |
| `fallback_rag_only` | LLM 不可用，返回原文 |

### GET `/api/status` - 系统状态

```bash
curl http://localhost:8000/api/status
```

```json
{
  "status": "ready",
  "initialized": true,
  "collection": {
    "vectors_count": 148,
    "backend": "FAISS (In-Memory)"
  }
}
```

---

## 💡 孟子的说话风格

系统 Prompt 设计参考了"微信孟子"风格：

✅ **言简意赅**：不长篇大论，单刀直入  
✅ **辩论思维**：用反问和类比启发，不直接说教  
✅ **现代白话**：像个学会用微信的长辈，不用"孟子曰"  
✅ **性善论**：引导用户发现内心本有的"良知"  

**示例对话**
```
用户: 人生的意义是什么？

孟子: 你问人生的意义，这问题问得好！
    人生啊，就像是一棵树，不是为了长得高大，
    而是为了根深叶茂，给世界带来阴凉。
    所以意义不在于你得到了多少，
    而在于你贡献了多少。
```

---

## 🛠 开发指南

### 修改孟子风格

编辑 `/backend/app/llm/client.py` 中的 `MENCIUS_SYSTEM_PROMPT`：

```python
MENCIUS_SYSTEM_PROMPT = """【Role】
你是战国时期的思想家孟子。你现在通过微信与现代人交流。
...
"""
```

### 添加自定义问题路由

在 `/backend/app/api/routes.py` 中添加新的路由：

```python
@router.post("/api/custom")
async def custom_endpoint(request: CustomRequest):
    # 你的逻辑
    pass
```

### 前端组件开发

修改 `/frontend/src/components/ChatInterface.vue` 自定义 UI

---

## 📊 数据流向

1. **初始化阶段**
   - 加载 `/data/raw/孟子译注.txt`
   - 分段后向量化
   - 导入 FAISS 内存索引 (148 个节点)

2. **用户提问阶段**
   - 用户问题向量化
   - FAISS 检索 Top-3 相关段落
   - 组装 Prompt：系统提示 + 上下文 + 问题

3. **LLM 生成阶段**
   - 调用 GLM-4-Flash API
   - 返回孟子风格回答

4. **应急回退阶段**
   - 如果 LLM 失败，直接返回原文段落

---

## ⚙️ 环境变量

创建 `backend/.env`：

```ini
# 必需（从 https://open.bigmodel.cn/ 获取）
GLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 可选
DEBUG=True
BACKEND_PORT=8000
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-mpnet-base-v2
```

---

## 📦 技术栈

| 组件     | 技术                      |
| -------- | ------------------------- |
| 前端框架 | Vue 3 + TypeScript + Vite |
| 后端框架 | FastAPI + Uvicorn         |
| LLM      | 智谱 GLM-4-Flash API      |
| 向量库   | FAISS (内存)              |
| 向量模型 | sentence-transformers     |
| 数据源   | 孟子译注 (txt)            |

---

## 📄 许可证

MIT License

---

## 🤝 反馈与贡献

欢迎提交 Issue 和 Pull Request！

## 常见问题

### ❓ "Module not found" 错误
```bash
# 确保虚拟环境激活并安装了依赖
conda activate men
pip install -r backend/requirements.txt
```

### ❓ 前端无法连接后端
- 检查后端是否运行在 8000 端口：`http://localhost:8000`
- 访问 `http://localhost:8000/health` 测试连接
- 检查浏览器控制台 (F12) 的 Network 选项卡查看 API 调用

### ❓ 智谱 GLM4 API 错误
- 验证 `.env` 中的 `GLM_API_KEY` 是否正确
- 检查 API Key 是否已激活（在 [智谱平台](https://open.bigmodel.cn/) 查看）
- 查看后端日志获取详细错误信息


### 修改聊天界面样式

编辑 `frontend/src/components/ChatInterface.vue` 的 `<style>` 部分。

## 贡献指南

1. 创建功能分支：`git checkout -b feature/your-feature`
2. 提交更改：`git commit -m "Add your feature"`
3. 推送分支：`git push origin feature/your-feature`
4. 创建 Pull Request

## 许可证

本项目仅供学习使用。孟子译注的版权属于原作者。
