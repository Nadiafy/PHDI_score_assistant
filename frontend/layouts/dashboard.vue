<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Sidebar -->
    <aside class="w-64 bg-white border-r flex flex-col shadow-sm">
      <div class="h-16 flex items-center px-6 font-bold text-xl text-green-700 border-b">
        🌿 PHDI Tracker
      </div>
      <nav class="flex-1 px-4 py-6 space-y-2">
        <NuxtLink to="/dashboard" class="flex items-center px-4 py-2 text-gray-700 hover:bg-green-50 hover:text-green-700 rounded-lg transition-colors" active-class="bg-green-50 text-green-700 font-medium">
          Dashboard
        </NuxtLink>
        <NuxtLink to="/chatbot" class="flex items-center px-4 py-2 text-gray-700 hover:bg-green-50 hover:text-green-700 rounded-lg transition-colors" active-class="bg-green-50 text-green-700 font-medium">
          Chatbot
        </NuxtLink>
        <NuxtLink to="/profile" class="flex items-center px-4 py-2 text-gray-700 hover:bg-green-50 hover:text-green-700 rounded-lg transition-colors" active-class="bg-green-50 text-green-700 font-medium">
          Profile
        </NuxtLink>
      </nav>
      <div class="p-4 border-t">
        <button @click="logout" class="w-full px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg text-left transition-colors font-medium">
          Sign out
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto bg-gray-50 p-8">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const logout = () => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('auth_token')
  }
  router.push('/')
}
</script>
