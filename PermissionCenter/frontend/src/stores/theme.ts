import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const isDark = ref(localStorage.getItem('iam_theme') === 'dark')

  function applyTheme() {
    document.documentElement.classList.toggle('dark', isDark.value)
    localStorage.setItem('iam_theme', isDark.value ? 'dark' : 'light')
  }

  function toggle() {
    isDark.value = !isDark.value
    applyTheme()
  }

  // Apply on init
  applyTheme()

  return { isDark, toggle }
})
