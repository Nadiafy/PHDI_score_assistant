<template>
  <div class="max-w-2xl mx-auto py-8">
    <div class="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
      <h1 class="text-3xl font-bold text-gray-900 mb-6">Profile Settings</h1>
      
      <div class="space-y-8">
        <!-- Account Info -->
        <div>
           <h2 class="text-lg font-bold text-gray-800 mb-3">Web Account</h2>
           <div class="bg-gray-50 p-4 rounded-xl border border-gray-200">
              <span class="block text-sm text-gray-500 mb-1">Signed in via Google as:</span>
              <span class="font-medium text-gray-900">User Email Protected (JWT bound)</span>
           </div>
        </div>

        <!-- Telegram Connection -->
        <div>
           <h2 class="text-lg font-bold text-gray-800 mb-3">Integrations</h2>
           <div class="bg-blue-50/50 p-6 rounded-xl border border-blue-100 relative overflow-hidden">
              <div class="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                 <div>
                    <h3 class="font-bold text-blue-900 flex items-center gap-2">
                       <svg class="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 24 24"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.892-.668 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
                       Telegram Bot
                    </h3>
                    <p class="text-blue-800 text-sm mt-1 max-w-sm">Connect your Telegram account to log meals on the go and have scores synchronized instantly.</p>
                 </div>
                 
                 <button @click="connectTelegram" class="shrink-0 bg-blue-500 hover:bg-blue-600 text-white font-medium py-2.5 px-5 rounded-lg shadow-sm shadow-blue-500/30 transition-all flex items-center gap-2">
                    <span v-if="!linking">Connect Telegram</span>
                    <span v-else>Generating link...</span>
                 </button>
              </div>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

definePageMeta({ layout: 'dashboard' })

const linking = ref(false)

const connectTelegram = async () => {
   linking.value = true
   try {
     const token = localStorage.getItem('auth_token')
     const res = await fetch('http://localhost:8000/api/auth/link-telegram', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
     })
     const data = await res.json()
     if (data.link_url) {
        window.open(data.link_url, '_blank')
     }
   } catch(e) {
     console.error(e)
   } finally {
     linking.value = false
   }
}
</script>
