<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-50 to-green-100">
    <div class="bg-white p-10 rounded-3xl shadow-2xl max-w-md w-full text-center border border-green-100">
      <div class="text-6xl mb-6">🌍</div>
      <h1 class="text-3xl font-extrabold text-gray-900 mb-2">PHDI Score</h1>
      <p class="text-gray-500 mb-8 font-medium">Track your planetary health diet impact and build better habits.</p>
      
      <div class="flex flex-col items-center justify-center space-y-4">
        <!-- GoogleLogin component provided by vue3-google-login -->
        <ClientOnly>
          <GoogleLogin :callback="handleLogin" auto-login />
        </ClientOnly>
        
        <div class="mt-8 text-sm text-gray-400">
          <p>Don't have Google configured?</p>
          <button @click="devLogin" class="mt-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition font-medium">
            Bypass for local dev
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const handleLogin = async (response) => {
  try {
    const res = await fetch('http://localhost:8000/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: response.credential })
    })
    const data = await res.json()
    if (data.access_token) {
      if (typeof window !== 'undefined') localStorage.setItem('auth_token', data.access_token)
      router.push('/dashboard')
    }
  } catch (e) {
    console.error(e)
  }
}

const devLogin = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: 'dev_token' })
    })
    const data = await res.json()
    if (data.access_token) {
      if (typeof window !== 'undefined') localStorage.setItem('auth_token', data.access_token)
      router.push('/dashboard')
    }
  } catch (e) {
    console.error(e)
  }
}
</script>
