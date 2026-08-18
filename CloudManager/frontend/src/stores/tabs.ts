import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'

export interface TabItem {
  path: string
  title: string
  name: string
  closable: boolean
}

export const useTabStore = defineStore('tabs', () => {
  const tabs = ref<TabItem[]>([])
  const activeTab = ref('')

  function addTab(route: RouteLocationNormalized) {
    const { path, meta, name } = route
    if (meta?.hidden) return

    const exists = tabs.value.find((t) => t.path === path)
    if (!exists) {
      tabs.value.push({
        path,
        title: (meta?.title as string) || (name as string),
        name: name as string,
        closable: path !== '/dashboard',
      })
    }
    activeTab.value = path
  }

  function removeTab(path: string) {
    const idx = tabs.value.findIndex((t) => t.path === path)
    if (idx === -1) return

    tabs.value.splice(idx, 1)
    if (activeTab.value === path) {
      const newTab = tabs.value[Math.min(idx, tabs.value.length - 1)]
      activeTab.value = newTab?.path || '/dashboard'
    }
  }

  function clearTabs() {
    tabs.value = []
    activeTab.value = ''
  }

  return { tabs, activeTab, addTab, removeTab, clearTabs }
})
