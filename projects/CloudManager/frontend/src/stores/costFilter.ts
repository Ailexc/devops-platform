import { defineStore } from 'pinia'
import { reactive } from 'vue'

/**
 * 成本模块全局筛选状态（方案 A：跨页面保持，sessionStorage 持久化）
 * 维度：云厂商 / 云账号 / 区域 / 部门 / 应用 / 月份
 */
export const useCostFilterStore = defineStore('costFilter', () => {
  const KEY = 'cost_global_filter'

  const saved = (() => {
    try {
      return JSON.parse(sessionStorage.getItem(KEY) || '{}')
    } catch {
      return {}
    }
  })()

  const filter = reactive<Record<string, string>>({
    cloud: saved.cloud || '',
    account: saved.account || '',
    region: saved.region || '',
    department: saved.department || '',
    application: saved.application || '',
    month: saved.month || '',
  })

  function set(key: string, val: string) {
    filter[key] = val
    persist()
  }

  function reset() {
    filter.cloud = ''
    filter.account = ''
    filter.region = ''
    filter.department = ''
    filter.application = ''
    filter.month = ''
    persist()
  }

  function persist() {
    try {
      sessionStorage.setItem(KEY, JSON.stringify({ ...filter }))
    } catch { /* 忽略 */ }
  }

  /** 生成请求参数（去掉空值） */
  function params(): Record<string, string> {
    const p: Record<string, string> = {}
    Object.keys(filter).forEach((k) => {
      if (filter[k]) p[k] = filter[k]
    })
    return p
  }

  return { filter, set, reset, persist, params }
})
