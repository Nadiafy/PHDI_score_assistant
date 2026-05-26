import vue3GoogleLogin from 'vue3-google-login'
import { defineNuxtPlugin, useRuntimeConfig } from '#app'

export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  nuxtApp.vueApp.use(vue3GoogleLogin, {
    clientId: config.public.googleClientId
  })
})
