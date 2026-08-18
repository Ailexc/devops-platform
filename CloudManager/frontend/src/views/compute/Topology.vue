<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { topologyApi } from '@/api'
import { useGlobalStore } from '@/stores/global'

const globalStore = useGlobalStore()
const loading = ref(false)
const nodes = ref<any[]>([])
const edges = ref<any[]>([])

const typeColors: Record<string, string> = {
  instance: '#1890ff',
  vpc: '#52c41a',
  security_group: '#faad14',
  subnet: '#722ed1',
  disk: '#eb2f96',
}
const typeLabels: Record<string, string> = {
  instance: '云主机',
  vpc: 'VPC',
  security_group: '安全组',
}

async function loadTopology() {
  loading.value = true
  try {
    const { data } = await topologyApi.get(undefined, globalStore.region || undefined)
    nodes.value = data.nodes
    edges.value = data.edges
  } catch { /* 静默 */ } finally { loading.value = false }
}

function getNodesByType(type: string) {
  return nodes.value.filter(n => n.type === type)
}

onMounted(loadTopology)
</script>

<template>
  <div>
    <a-page-header title="🔗 资源拓扑" @back="$router.back()">
      <template #extra>
        <a-space>
          <a-select v-model:value="globalStore.region" placeholder="全部地域" allow-clear style="width: 150px" @change="loadTopology">
            <a-select-option value="cn-hangzhou">cn-hangzhou</a-select-option>
            <a-select-option value="cn-shanghai">cn-shanghai</a-select-option>
            <a-select-option value="cn-beijing">cn-beijing</a-select-option>
            <a-select-option value="us-east-1">us-east-1</a-select-option>
          </a-select>
          <a-button @click="loadTopology">🔄 刷新</a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-row :gutter="16" style="margin-bottom: 16px">
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="总节点数" :value="nodes.length" :value-style="{ color: '#1890ff' }" />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="关联关系数" :value="edges.length" :value-style="{ color: '#52c41a' }" />
          </a-card>
        </a-col>
        <a-col :span="8">
          <a-card size="small">
            <a-statistic title="主机数" :value="nodes.filter(n => n.type === 'instance').length" :value-style="{ color: '#722ed1' }" />
          </a-card>
        </a-col>
      </a-row>

      <!-- 拓扑可视化（简化版：按类型分组展示） -->
      <a-card v-for="type in ['instance', 'vpc', 'security_group']" :key="type" :title="`${typeLabels[type] || type} (${getNodesByType(type).length})`" style="margin-bottom: 16px">
        <a-table
          :columns="[
            { title: '名称', dataIndex: 'label' },
            { title: '资源ID', dataIndex: 'cloud_id' },
            { title: '地域', dataIndex: 'region', width: 130 },
            { title: '状态', dataIndex: 'status', width: 100 },
            { title: '规格', dataIndex: 'spec', width: 140 },
            { title: '关联数', key: 'rels', width: 80 },
          ]"
          :data-source="getNodesByType(type)"
          row-key="id"
          size="small"
          :pagination="{ pageSize: 10, showTotal: (t: number) => `共 ${t} 条` }"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'status'">
              <a-tag :color="record.status === 'running' ? 'green' : record.status === 'stopped' ? 'red' : 'blue'">
                {{ record.status }}
              </a-tag>
            </template>
            <template v-if="column.key === 'rels'">
              <a-badge :count="edges.filter(e => e.source === record.id || e.target === record.id).length" show-zero />
            </template>
          </template>
        </a-table>
      </a-card>
    </a-spin>
  </div>
</template>
