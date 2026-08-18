<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { resourceApi, graphApi } from '@/api'
import type { Resource, GraphData } from '@/types'

const props = defineProps<{
  open: boolean
  resourceId?: number
}>()

const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()
const router = useRouter()

const tab = ref('basic')
const loading = ref(false)
const detail = ref<Resource | null>(null)
const neighbors = ref<GraphData>({ nodes: [], edges: [] })
const changes = ref<any[]>([])
const impact = ref<any>(null)

async function load() {
  if (!props.resourceId) return
  loading.value = true
  detail.value = null
  neighbors.value = { nodes: [], edges: [] }
  changes.value = []
  impact.value = null
  try {
    const [d, nb, ch, im] = await Promise.all([
      resourceApi.get(props.resourceId),
      graphApi.neighbors(props.resourceId),
      resourceApi.changes(props.resourceId),
      graphApi.impact(props.resourceId),
    ])
    detail.value = d.data
    neighbors.value = nb.data
    changes.value = ch.data
    impact.value = im.data
  } catch {
    message.error('加载资源详情失败')
  } finally {
    loading.value = false
  }
}

watch(() => props.open, (v) => {
  if (v && props.resourceId) {
    tab.value = 'basic'
    load()
  }
})

function close() {
  emit('update:open', false)
}
</script>

<template>
  <a-drawer :open="open" :width="520" title="🔍 资源详情" @update:open="emit('update:open', $event)">
    <a-spin :spinning="loading">
      <a-tabs v-model:activeKey="tab">
        <a-tab-pane key="basic" tab="基础信息">
          <a-descriptions v-if="detail" :column="2" bordered size="small">
            <a-descriptions-item label="名称">{{ detail.resource_name }}</a-descriptions-item>
            <a-descriptions-item label="类型">{{ detail.resource_type_display }}</a-descriptions-item>
            <a-descriptions-item label="资源ID">{{ detail.cloud_resource_id }}</a-descriptions-item>
            <a-descriptions-item label="状态">{{ detail.status }}</a-descriptions-item>
            <a-descriptions-item label="规格">{{ detail.spec || '-' }}</a-descriptions-item>
            <a-descriptions-item label="地域">{{ detail.region }}</a-descriptions-item>
            <a-descriptions-item label="资源归属">
              <a-tag :color="detail.managed_by === 'self' ? 'orange' : 'blue'">
                {{ detail.managed_by_display || (detail.managed_by === 'self' ? '自建' : '云资源') }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="所属环境">{{ detail.environment_name || '-' }}</a-descriptions-item>
            <a-descriptions-item label="云账号">{{ detail.account_name }}</a-descriptions-item>
            <a-descriptions-item label="来源系统">{{ detail.source_system || 'cmdb' }}</a-descriptions-item>
          </a-descriptions>
          <a-button v-if="detail" type="primary" size="small" style="margin-top: 12px" @click="router.push(`/resources/${resourceId}`)">
            查看完整详情
          </a-button>
        </a-tab-pane>

        <a-tab-pane key="relation" tab="依赖关系">
          <a-table
            :columns="[{ title: '关系', dataIndex: 'relation_type' }, { title: '对象', dataIndex: 'name' }, { title: '强度', dataIndex: 'strength' }]"
            :data-source="neighbors.edges.map((e) => {
              const other = e.source === `res:${resourceId}` ? e.target : e.source
              const node = neighbors.nodes.find((n) => n.id === other)
              return { key: `${e.source}-${e.target}`, name: node?.name || other, relation_type: e.relation_type, strength: e.strength }
            })"
            row-key="key"
            size="small"
            :pagination="false"
          />
        </a-tab-pane>

        <a-tab-pane key="impact" tab="影响面">
          <template v-if="impact">
            <a-row :gutter="8">
              <a-col :span="8"><a-statistic title="强影响" :value="impact.summary.high" value-style="color:#ef4444;font-size:20px" /></a-col>
              <a-col :span="8"><a-statistic title="中影响" :value="impact.summary.medium" value-style="color:#f97316;font-size:20px" /></a-col>
              <a-col :span="8"><a-statistic title="间接" :value="impact.summary.low" value-style="color:#3b82f6;font-size:20px" /></a-col>
            </a-row>
            <a-table
              :columns="[{ title: '受影响资源', dataIndex: 'name' }, { title: '级别', dataIndex: 'severity' }]"
              :data-source="impact.nodes.slice(0, 10)"
              row-key="id"
              size="small"
              :pagination="false"
              style="margin-top: 12px"
            />
          </template>
          <a-empty v-else description="暂无影响面数据" />
        </a-tab-pane>

        <a-tab-pane key="changes" tab="变更历史">
          <a-table
            :columns="[{ title: '操作', dataIndex: 'action' }, { title: '操作人', dataIndex: 'operator' }, { title: '时间', dataIndex: 'created_at' }]"
            :data-source="changes"
            row-key="id"
            size="small"
            :pagination="false"
          />
        </a-tab-pane>
      </a-tabs>
    </a-spin>
  </a-drawer>
</template>
