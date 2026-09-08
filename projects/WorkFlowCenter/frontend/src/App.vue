<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

onMounted(() => {
  // 检查本地存储的 token
  const token = localStorage.getItem('token')
  if (token) {
    authStore.setToken(token)
    authStore.fetchUser()
  }
})
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
}
</style>