<template>
  <div class="global-filter fade-in">
    <span class="gf-label">🌐 成本分析范围</span>
    <span class="gf-dim">云</span>
    <a-select v-model:value="f.cloud" placeholder="全部云" allow-clear style="width: 108px">
      <a-select-option v-for="c in options.clouds" :key="c" :value="c">{{ cloudName(c) }}</a-select-option>
    </a-select>
    <span class="gf-dim">账号</span>
    <a-select v-model:value="f.account" placeholder="全部账号" allow-clear style="width: 124px">
      <a-select-option v-for="a in options.accounts" :key="a" :value="a">{{ a }}</a-select-option>
    </a-select>
    <span class="gf-dim">区域</span>
    <a-select v-model:value="f.region" placeholder="全部区域" allow-clear style="width: 112px">
      <a-select-option v-for="r in options.regions" :key="r" :value="r">{{ r }}</a-select-option>
    </a-select>
    <span class="gf-dim">部门</span>
    <a-select v-model:value="f.department" placeholder="全部部门" allow-clear style="width: 112px">
      <a-select-option v-for="d in options.departments" :key="d" :value="d">{{ d }}</a-select-option>
    </a-select>
    <span class="gf-dim">应用</span>
    <a-select v-model:value="f.application" placeholder="全部应用" allow-clear style="width: 112px">
      <a-select-option v-for="a in options.applications" :key="a" :value="a">{{ a }}</a-select-option>
      <a-select-option value="未归属">未归属</a-select-option>
    </a-select>
    <span class="gf-dim">月份</span>
    <a-select v-model:value="f.month" placeholder="全部月份" allow-clear style="width: 108px">
      <a-select-option v-for="m in months" :key="m" :value="m">{{ m }}</a-select-option>
    </a-select>
    <a-button size="small" @click="onReset">重置</a-button>
    <span v-if="activeCount" class="gf-active">{{ activeCount }} 项已筛选</span>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { costApi } from '@/api'
import { useCostFilterStore } from '@/stores/costFilter'

const store = useCostFilterStore()
const f = store.filter

const providerMap: Record<string, string> = { aws: 'AWS', aliyun: '阿里云', tencent: '腾讯云', mock: 'Mock' }
function cloudName(c: string) { return providerMap[c] || c }

const options = reactive({
  clouds: [] as string[],
  accounts: [] as string[],
  regions: [] as string[],
  departments: [] as string[],
  applications: [] as string[],
})
const months = ref<string[]>([])

const activeCount = computed(() => Object.values(f).filter(Boolean).length)

// 生成近 12 个月份
function genMonths() {
  const arr: string[] = []
  const d = new Date()
  for (let i = 0; i < 12; i++) {
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    arr.push(`${y}-${m}`)
    d.setMonth(d.getMonth() - 1)
  }
  months.value = arr
}

async function load() {
  try {
    const { data } = await costApi.globalFilters()
    options.clouds = data.clouds || []
    options.accounts = data.accounts || []
    options.regions = data.regions || []
    options.departments = data.departments || []
    options.applications = data.applications || []
    // 清理不在当前用户权限范围内的筛选值（如普通员工登录后，越权筛选值自动清空）
    const f = store.filter
    if (f.cloud && !options.clouds.includes(f.cloud)) f.cloud = ''
    if (f.account && !options.accounts.includes(f.account)) f.account = ''
    if (f.region && !options.regions.includes(f.region)) f.region = ''
    if (f.department && !options.departments.includes(f.department)) f.department = ''
    if (f.application && f.application !== '未归属' && !options.applications.includes(f.application)) f.application = ''
  } catch { /* 静默 */ }
}

function onReset() {
  store.reset()
}

// 筛选变化 → 持久化（页面通过 watch store.filter 联动）
watch(
  () => ({ ...f }),
  () => store.persist(),
  { deep: true },
)

onMounted(() => {
  genMonths()
  load()
})
</script>

<style scoped>
.global-filter { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; background: white; border: 1px solid var(--cm-border-default); border-radius: var(--cm-radius-lg); padding: 10px 14px; margin-bottom: 16px; }
.gf-label { font-size: var(--cm-text-sm); font-weight: var(--cm-font-semibold); color: var(--cm-text-primary); margin-right: 2px; }
.gf-dim { font-size: 12px; color: var(--cm-text-tertiary); margin-left: 2px; }
.gf-active { font-size: 12px; color: #7C3AED; font-weight: 600; }
.fade-in { animation: fadeIn 0.3s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>
