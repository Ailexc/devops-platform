<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { graphApi } from '@/api'
import TopologyCompose from '@/components/topo/TopologyCompose.vue'

const envId = ref<number>()
const label = ref('加载中...')

onMounted(async () => {
  try {
    const apps = await graphApi.applications()
    const first = apps.data[0]
    if (!first) return
    const envs = await graphApi.applicationEnvs(first.id)
    const prod = envs.data.find((e) => e.env_type === 'prod') || envs.data[0]
    if (!prod) return
    envId.value = prod.id
    label.value = `${first.name} / ${prod.name}`
  } catch {
    label.value = '加载失败'
  }
})
</script>

<template>
  <div>
    <a-page-header title="🧭 图谱交互 Demo v3" :sub-title="`示例数据：${label}`" />

    <TopologyCompose v-if="envId" :env-id="envId" />

    <a-alert
      type="info"
      show-icon
      style="margin-top: 12px"
      message="交互说明：方框=节点（服务/资源区分），区域背景随图整体缩放；右上角切换系统构成/上下游、按区域过滤、浏览/编辑；编辑模式下增删改依赖会立即在图上以虚边预览，提交后生成「关系变更工单」，审批通过才落库。"
    />
  </div>
</template>
