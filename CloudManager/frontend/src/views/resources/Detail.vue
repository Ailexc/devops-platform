<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { resourceApi, graphApi, scenarioApi } from '@/api'
import type { Resource, GraphData, ImpactResult, GraphNode, Scenario } from '@/types'
import GraphView from '@/components/GraphView.vue'
import ResourcePreview from '@/components/ResourcePreview.vue'

const route = useRoute()
const router = useRouter()
const resource = ref<Resource | null>(null)
const neighbors = ref<GraphData>({ nodes: [], edges: [] })
const impact = ref<ImpactResult | null>(null)
const changes = ref<any[]>([])
const securityRules = ref<any[]>([])
const loading = ref(false)
const activeTab = ref('graph')
const previewResourceId = ref<number | null>(null)
const scenarioModalVisible = ref(false)
const scenarios = ref<Scenario[]>([])
const submitting = ref(false)
const applyForm = ref({
  scenario_id: undefined as number | undefined,
  name: '',
})

const severityColors: Record<string, string> = {
  high: 'red',
  medium: 'orange',
  low: 'blue',
}

async function loadAll() {
  const id = Number(route.params.id)
  if (!id) return
  previewResourceId.value = null
  loading.value = true
  try {
    const [res, nb, imp, ch, rules] = await Promise.all([
      resourceApi.get(id),
      graphApi.neighbors(id),
      graphApi.impact(id),
      resourceApi.changes(id),
      resourceApi.securityRules(id),
    ])
    resource.value = res.data
    neighbors.value = nb.data
    impact.value = imp.data
    changes.value = ch.data
    securityRules.value = rules.data
  } catch {
    message.error('加载资源详情失败')
  } finally {
    loading.value = false
  }
}

async function handleNodeClick(node: GraphNode) {
  if (node.id?.startsWith('res:')) {
    previewResourceId.value = Number(node.id.split(':')[1])
  } else {
    message.info(`「${node.name}」属于 ${node.category}，关系已在其所在页面展示`)
  }
}

async function openScenario() {
  try {
    const { data } = await scenarioApi.list({ page_size: 50 })
    scenarios.value = data.results || data
    scenarioModalVisible.value = true
  } catch {
    message.error('加载场景模板失败')
  }
}

async function submitScenario() {
  if (!resource.value) return
  if (!applyForm.value.scenario_id || !applyForm.value.name) {
    message.warning('请选择场景并填写操作名称')
    return
  }
  submitting.value = true
  try {
    const { data } = await scenarioApi.apply(applyForm.value.scenario_id, {
      title: `${resource.value.resource_name} - ${applyForm.value.name}`,
      request_content: {
        resource_id: resource.value.id,
        resource_type: resource.value.resource_type,
        cloud_resource_id: resource.value.cloud_resource_id,
        name: applyForm.value.name,
        region: resource.value.region,
      },
    })
    message.success(`场景工单已提交：${data.ticket_no}`)
    scenarioModalVisible.value = false
    router.push(`/ticket/detail/${data.ticket_id}`)
  } catch {
    message.error('提交失败')
  } finally {
    submitting.value = false
  }
}

watch(() => route.params.id, loadAll)
onMounted(loadAll)

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/compute/instances')
}
</script>

<template>
  <div>
    <a-page-header title="资源详情" @back="goBack">
      <template #extra>
        <a-button type="primary" @click="openScenario">🧩 发起运维场景</a-button>
        <a-button @click="loadAll">🔄 刷新</a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <a-card v-if="resource" style="margin-bottom: 16px">
        <a-descriptions :column="3" bordered size="small">
          <a-descriptions-item label="资源名称">{{ resource.resource_name }}</a-descriptions-item>
          <a-descriptions-item label="资源ID">{{ resource.cloud_resource_id }}</a-descriptions-item>
          <a-descriptions-item label="类型">{{ resource.resource_type_display }}</a-descriptions-item>
          <a-descriptions-item label="云账号">{{ resource.account_name }}</a-descriptions-item>
          <a-descriptions-item label="地域/可用区">{{ resource.region }} {{ resource.zone || '' }}</a-descriptions-item>
          <a-descriptions-item label="规格">{{ resource.spec || '-' }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="resource.status === 'running' ? 'green' : resource.status === 'stopped' ? 'red' : 'blue'">
              {{ resource.status }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="来源系统">
            <a-tag>{{ resource.source_system || 'cmdb' }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="同步方式">{{ resource.sync_mode || 'manual' }}</a-descriptions-item>
        </a-descriptions>
      </a-card>

      <a-card>
        <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="graph" tab="🔗 关系与上下游">
            <GraphView :nodes="neighbors.nodes" :edges="neighbors.edges" height="520px" @node-click="handleNodeClick" />
            <ResourcePreview
              v-if="previewResourceId"
              :resource-id="previewResourceId"
              @close="previewResourceId = null"
            />
            <a-alert
              type="info"
              show-icon
              message="实线为强制依赖，虚线为软依赖；点击资源节点可进入其详情查看上下游"
              style="margin-top: 12px"
            />
          </a-tab-pane>

          <a-tab-pane key="impact" tab="⚠️ 影响面分析">
            <template v-if="impact">
              <a-row :gutter="16" style="margin-bottom: 16px">
                <a-col :span="6"><a-statistic title="强影响(硬依赖)" :value="impact.summary.high" :value-style="{ color: '#ef4444' }" /></a-col>
                <a-col :span="6"><a-statistic title="中影响(软依赖)" :value="impact.summary.medium" :value-style="{ color: '#f97316' }" /></a-col>
                <a-col :span="6"><a-statistic title="间接影响" :value="impact.summary.low" :value-style="{ color: '#3b82f6' }" /></a-col>
                <a-col :span="6"><a-statistic title="单点依赖(SPOF)" :value="impact.summary.spof.length" :value-style="{ color: '#7c3aed' }" /></a-col>
              </a-row>
              <a-table
                :columns="[
                  { title: '受影响资源', dataIndex: 'name' },
                  { title: '类型', dataIndex: 'resource_type' },
                  { title: '关系', dataIndex: 'relation_type' },
                  { title: '强度', dataIndex: 'strength' },
                  { title: '影响级别', dataIndex: 'severity' },
                ]"
                :data-source="impact.nodes"
                row-key="id"
                size="small"
                :pagination="{ pageSize: 10 }"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.dataIndex === 'strength'">
                    <a-tag :color="record.strength === 'hard' ? 'purple' : 'default'">
                      {{ record.strength === 'hard' ? '强制' : '软' }}
                    </a-tag>
                  </template>
                  <template v-if="column.dataIndex === 'severity'">
                    <a-tag :color="severityColors[record.severity]">{{ record.severity }}</a-tag>
                  </template>
                </template>
              </a-table>
            </template>
            <a-empty v-else description="暂无影响面数据" />
          </a-tab-pane>

          <a-tab-pane key="security" tab="🛡️ 网络与安全规则">
            <a-table
              :columns="[
                { title: '安全组', dataIndex: 'security_group_name' },
                { title: '方向', dataIndex: 'direction_display' },
                { title: '协议', dataIndex: 'protocol' },
                { title: '端口', dataIndex: 'port_range' },
                { title: '源', dataIndex: 'source' },
                { title: '动作', dataIndex: 'action_display' },
              ]"
              :data-source="securityRules"
              row-key="id"
              size="small"
              :pagination="false"
            />
          </a-tab-pane>

          <a-tab-pane key="changes" tab="📜 变更历史">
            <a-table
              :columns="[
                { title: '操作', dataIndex: 'action' },
                { title: '操作人', dataIndex: 'operator' },
                { title: '来源', dataIndex: 'source' },
                { title: '关联工单', dataIndex: 'ticket_id' },
                { title: '时间', dataIndex: 'created_at' },
              ]"
              :data-source="changes"
              row-key="id"
              size="small"
              :pagination="{ pageSize: 10 }"
            />
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </a-spin>

    <a-modal v-model:open="scenarioModalVisible" title="🧩 发起运维场景" :confirm-loading="submitting" @ok="submitScenario">
      <a-form layout="vertical">
        <a-form-item label="场景模板" required>
          <a-select v-model:value="applyForm.scenario_id" placeholder="选择场景">
            <a-select-option v-for="s in scenarios" :key="s.id" :value="s.id">
              {{ s.icon }} {{ s.name }}（{{ s.step_count }} 步）
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="操作名称" required>
          <a-input v-model:value="applyForm.name" placeholder="如：安全组变更" />
        </a-form-item>
      </a-form>
      <a-alert type="info" show-icon :message="`将自动带入当前资源上下文（${resource?.resource_name || ''}），提交后进入工单审批`" />
    </a-modal>
  </div>
</template>
