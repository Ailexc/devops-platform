import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 全局上下文：云账号 / 地域切换，所有资源页面统一消费
 */
export const useGlobalStore = defineStore('global', () => {
  const accountId = ref<number | null>(null)
  const region = ref('')

  function setAccount(id: number | null) {
    accountId.value = id
  }

  function setRegion(value: string) {
    region.value = value
  }

  return { accountId, region, setAccount, setRegion }
})
