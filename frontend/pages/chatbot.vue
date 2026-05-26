<template>
  <div class="h-[calc(100vh-4rem)] flex flex-col max-w-4xl mx-auto py-8">
    <div class="bg-white rounded-3xl shadow-xl overflow-hidden flex flex-col border border-gray-100 h-full">
      <!-- Header -->
      <div class="p-6 border-b bg-green-50/50 backdrop-blur-xl flex items-center justify-between">
        <h1 class="text-xl font-bold text-green-800">PHDI Assistant</h1>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
          <span class="text-xs text-green-600 uppercase tracking-widest font-semibold">Live System</span>
        </div>
      </div>

      <!-- Chat Container -->
      <div ref="chatContainer" class="flex-1 overflow-y-auto p-6 flex flex-col gap-4 scroll-smooth bg-gray-50">
        <div v-for="(msg, idx) in messages" :key="idx" 
             :class="['chat-bubble', msg.role === 'user' ? 'bubble-user' : 'bubble-bot']">
          <div v-html="msg.text" class="prose prose-sm max-w-none" :class="msg.role === 'user' ? 'text-white' : 'text-gray-800'"></div>
          
          <!-- Result Card in Chat -->
          <div v-if="msg.isResult && result" class="mt-4 p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-gray-500 text-xs font-semibold uppercase">Sustainability Index</span>
              <span class="text-emerald-600 font-bold text-lg">{{ result.total_score }}/150</span>
            </div>
            <div class="w-full bg-gray-100 h-2 rounded-full overflow-hidden">
              <div class="bg-gradient-to-r from-emerald-500 to-green-400 h-full transition-all duration-1000" 
                   :style="{ width: (result.total_score / 150 * 100) + '%' }"></div>
            </div>
            
            <div class="mt-4">
               <h3 class="text-xs font-bold text-gray-400 uppercase mb-2">Breakdown</h3>
               <ul class="text-xs space-y-1 text-gray-600">
                 <li v-for="(score, cat) in result.component_scores" :key="cat" class="flex justify-between">
                   <span class="capitalize">{{ cat.replace(/_/g, ' ') }}</span>
                   <span :class="score >= 8 ? 'text-emerald-600 font-bold' : (score > 4 ? 'text-yellow-600 font-bold' : 'text-red-500 font-bold')">{{ score }} pts</span>
                 </li>
               </ul>
            </div>
          </div>
        </div>
        
        <div v-if="loading" class="bubble-bot chat-bubble italic text-gray-400 animate-pulse">
          Analyzing your food log...
        </div>
      </div>

      <!-- Input Bar -->
      <div class="p-6 border-t border-gray-100 bg-white">
        <div class="relative">
          <textarea v-model="userInput" 
                    @keydown.enter.prevent="sendMessage"
                    placeholder="E.g., For breakfast I had 2 boiled eggs and 200g of bread..." 
                    class="w-full bg-gray-50 border border-gray-200 rounded-2xl py-4 pl-4 pr-16 focus:outline-none focus:ring-2 focus:ring-green-500/50 transition-all resize-none h-24 text-gray-700 placeholder-gray-400"
          ></textarea>
          <button @click="sendMessage" 
                  :disabled="loading || !userInput.trim()"
                  class="absolute right-3 bottom-3 p-3 bg-green-600 hover:bg-green-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all shadow-lg shadow-green-900/20 text-white">
             Send
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'

definePageMeta({
  layout: 'dashboard'
})

const messages = ref([
  { role: 'bot', text: "Hello! I'm your Planetary Health Diet Index assistant. Tell me everything you ate and drank today, and I'll calculate your sustainability score." }
])
const userInput = ref('')
const loading = ref(false)
const result = ref(null)
const chatContainer = ref(null)

const sendMessage = async () => {
  if (!userInput.value.trim() || loading.value) return

  const userText = userInput.value
  messages.value.push({ role: 'user', text: userText })
  userInput.value = ''
  loading.value = true

  await scrollToBottom()

  try {
    const token = localStorage.getItem('auth_token')
    const response = await fetch('http://localhost:8000/calculate-phdi', {
      method: 'POST',
      headers: { 
         'Content-Type': 'application/json',
         'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ log_text: userText })
    })

    const data = await response.json()
    if (data.status === 'success') {
      result.value = data
      messages.value.push({ 
        role: 'bot', 
        text: `Your PHDI score for today is **${data.total_score} / 150 points**!`,
        isResult: true
      })
    } else {
      messages.value.push({ role: 'bot', text: "Sorry, I had trouble calculating your score. Please try again." })
    }
  } catch (error) {
    messages.value.push({ role: 'bot', text: "Connection error. Make sure the backend is running." })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-bubble {
  @apply max-w-[85%] rounded-2xl p-4 transition-all duration-300 shadow-sm;
}
.bubble-bot {
  @apply bg-white text-gray-800 self-start rounded-tl-none border border-gray-100;
}
.bubble-user {
  @apply bg-green-600 text-white self-end rounded-tr-none border border-green-500 shadow-md;
}
</style>
