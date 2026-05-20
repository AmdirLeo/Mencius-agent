<template>
  <div class="chat-container">
    <div class="chat-header">
      <h1>孟子智能体</h1>
      <p>向先贤请教人生之智慧</p>
    </div>
    
    <div class="messages" ref="messagesContainer">
      <div v-for="msg in messages" :key="msg.id" :class="['message', msg.role]">
        <div class="content">{{ msg.content }}</div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="content loading">孟子思考中<span>.</span><span>.</span><span>.</span></div>
      </div>
    </div>
    
    <div class="input-area">
      <input 
        v-model="input" 
        @keyup.enter="sendMessage"
        placeholder="请向孟子提问..." 
        :disabled="loading"
      />
      <button @click="sendMessage" :disabled="loading || !input.trim()">
        {{ loading ? '思考中' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { apiService } from '../services/api'

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

const messages = ref<Message[]>([
  { id: 0, role: 'assistant', content: '我是孟子，求仁由是也，非由外铄我也。有何疑惑，请问之。' }
])
const input = ref('')
const loading = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
let messageId = 1

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!input.value.trim() || loading.value) return
  
  const userMessage = input.value
  const history = messages.value
    .slice(-10)
    .map(({ role, content }) => ({ role, content }))

  messages.value.push({
    id: messageId++,
    role: 'user',
    content: userMessage
  })
  
  input.value = ''
  await scrollToBottom()
  
  loading.value = true
  
  try {
    const response = await apiService.ask(userMessage, history)
    messages.value.push({
      id: messageId++,
      role: 'assistant',
      content: response.answer
    })
  } catch (error) {
    messages.value.push({
      id: messageId++,
      role: 'assistant',
      content: '抱歉，孟子暂时无法回答，请稍后重试。'
    })
    console.error('API Error:', error)
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.chat-container {
  max-width: 900px;
  margin: 0 auto;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: white;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
}

.chat-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px 20px;
  text-align: center;
  border-bottom: 1px solid #e0e0e0;
}

.chat-header h1 {
  font-size: 28px;
  margin-bottom: 5px;
  font-weight: 600;
}

.chat-header p {
  font-size: 14px;
  opacity: 0.9;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  animation: slideIn 0.3s ease-in-out;
  align-items: flex-end;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  word-wrap: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
  font-size: 14px;
}

.message.user .content {
  background: #667eea;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .content {
  background: #e9ecef;
  color: #333;
  border-bottom-left-radius: 4px;
}

.content.loading {
  color: #999;
}

.content.loading span {
  animation: blink 1.4s infinite;
}

.content.loading span:nth-child(2) {
  animation-delay: 0.2s;
}

.content.loading span:nth-child(3) {
  animation-delay: 0.4s;
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s;
}

input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
}

button:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes blink {
  0%, 20%, 50%, 80%, 100% {
    opacity: 1;
  }
  40% {
    opacity: 0.5;
  }
  60% {
    opacity: 0.7;
  }
}

/* 响应式设计 */
@media (max-width: 600px) {
  .content {
    max-width: 85%;
  }
  
  .chat-header h1 {
    font-size: 22px;
  }
  
  .input-area {
    padding: 12px 16px;
  }
  
  input {
    padding: 10px 14px;
    font-size: 13px;
  }
  
  button {
    padding: 10px 18px;
    font-size: 13px;
  }
}
</style>
