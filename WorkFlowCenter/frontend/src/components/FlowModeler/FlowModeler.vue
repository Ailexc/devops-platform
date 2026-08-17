<template>
  <div class="flow-modeler">
    <div class="flow-toolbar">
      <el-button :icon="RefreshLeft" circle size="small" @click="undo" />
      <el-button :icon="RefreshRight" circle size="small" @click="redo" />
      <el-divider direction="vertical" />
      <el-button :icon="FullScreen" circle size="small" @click="fitViewAction" />
      <el-divider direction="vertical" />
      <el-button :icon="Delete" circle size="small" type="danger" plain @click="clearAll" />
      <el-button :icon="Download" circle size="small" @click="exportData" />
      <el-button :icon="Upload" circle size="small" @click="importData" />
    </div>
    <div class="flow-body">
      <div class="dnd-panel">
        <div class="dnd-title">流程节点</div>
        <div class="dnd-list">
          <div v-for="item in nodeTypes" :key="item.type" class="dnd-item" draggable="true" @dragstart="onDragStart($event, item)">
            <div class="dnd-icon" :style="{ background: item.color }">{{ item.icon }}</div>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
      <div class="graph-area" @drop="onDrop" @dragover.prevent>
        <VueFlow v-model:nodes="nodes" v-model:edges="edges" :default-edge-options="{ type: 'smoothstep', animated: true }" :connection-line-style="{ stroke: '#1677ff', strokeWidth: 2 }" :snap-to-grid="true" :snap-grid="[20, 20]" @node-click="onNodeClick" @pane-click="onPaneClick" @connect="onConnect" fit-view-on-init>
          <Background :gap="20" :size="1" />
          <Controls />
          <MiniMap />
        </VueFlow>
      </div>
      <div class="prop-panel" v-if="selectedNode">
        <div class="panel-header">
          <span>节点属性</span>
          <el-icon style="cursor:pointer" @click="selectedNode=null"><Close /></el-icon>
        </div>
        <div class="panel-body">
          <el-form label-position="top" size="small">
            <el-form-item label="节点名称">
              <el-input v-model="nodeConfig.name" @change="saveConfig" />
            </el-form-item>
            <el-form-item label="节点类型">
              <el-tag :color="nodeConfig.color" style="color:#fff;border:none">{{ nodeConfig.typeLabel }}</el-tag>
            </el-form-item>
            <template v-if="selectedNode.type === 'approve'">
              <el-divider content-position="left">审批设置</el-divider>
              <el-form-item label="审批方式">
                <el-radio-group v-model="nodeConfig.approval_type" @change="saveConfig">
                  <el-radio value="single">单人</el-radio>
                  <el-radio value="countersign">会签</el-radio>
                  <el-radio value="or_sign">或签</el-radio>
                </el-radio-group>
              </el-form-item>
              <el-form-item label="审批人">
                <el-select v-model="nodeConfig.assignee_type" @change="saveConfig">
                  <el-option label="指定人员" value="specified" />
                  <el-option label="发起人主管" value="manager" />
                  <el-option label="角色" value="role" />
                </el-select>
              </el-form-item>
            </template>
            <template v-if="selectedNode.type === 'service'">
              <el-divider content-position="left">服务设置</el-divider>
              <el-form-item label="能力编码">
                <el-select v-model="nodeConfig.capability_code" @change="saveConfig">
                  <el-option label="CMDB 创建主机" value="cmdb.create_host" />
                  <el-option label="DNS 添加记录" value="dns.add_record" />
                  <el-option label="邮件发送" value="mail.send" />
                  <el-option label="外部审批" value="external.approve" />
                </el-select>
              </el-form-item>
            </template>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import { RefreshLeft, RefreshRight, FullScreen, Delete, Download, Upload, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const props = defineProps({ modelValue: { type: Object, default: () => ({ nodes: [], edges: [] }) } })
const emit = defineEmits(['update:modelValue'])

const { fitView, addNodes, undo, redo, getNodes, getEdges } = useVueFlow()

const selectedNode = ref(null)
const nodes = ref([])
const edges = ref([])

const nodeTypes = [
  { type: 'start', label: '开始', color: '#52c41a', icon: '▶' },
  { type: 'approve', label: '审批', color: '#1677ff', icon: '✓' },
  { type: 'handle', label: '办理', color: '#fa8c16', icon: '⚡' },
  { type: 'service', label: '服务', color: '#722ed1', icon: '⚙' },
  { type: 'cc', label: '抄送', color: '#eb2f96', icon: '✉' },
  { type: 'condition', label: '条件', color: '#faad14', icon: '◇' },
  { type: 'end', label: '结束', color: '#f5222d', icon: '■' }
]

const nodeConfig = ref({ name: '', typeLabel: '', color: '', approval_type: 'single', assignee_type: 'specified', capability_code: '' })

function getColor(type) { return nodeTypes.find(n => n.type === type)?.color || '#999' }
function getLabel(type) { return nodeTypes.find(n => n.type === type)?.label || type }
function getIcon(type) { return nodeTypes.find(n => n.type === type)?.icon || '?' }

// 初始化数据
function initData() {
  if (props.modelValue?.nodes?.length) {
    nodes.value = props.modelValue.nodes.map(n => ({
      id: n.id,
      type: 'default',
      position: n.position || { x: 0, y: 0 },
      data: { ...n, _type: n.type },
      style: nodeStyle(n.type),
      class: 'wf-node'
    }))
    edges.value = (props.modelValue.edges || []).map((e, i) => ({
      id: e.id || `e${i}`,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#1677ff', strokeWidth: 2 }
    }))
  } else {
    nodes.value = [{ id: 'start_1', type: 'default', position: { x: 300, y: 100 }, data: { _type: 'start', text: '开始' }, style: nodeStyle('start'), class: 'wf-node' }]
    edges.value = []
  }
}

function nodeStyle(type) {
  const c = getColor(type)
  return { background: c, color: '#fff', border: `2px solid ${c}`, borderRadius: type === 'start' || type === 'end' ? '50%' : '8px', padding: '8px 16px', minWidth: '100px', textAlign: 'center', fontSize: '13px', fontWeight: '600', boxShadow: '0 2px 8px rgba(0,0,0,0.15)', cursor: 'grab' }
}

function syncData() {
  const data = {
    nodes: nodes.value.map(n => ({ id: n.id, type: n.data?._type || n.type, position: n.position, text: n.data?.text || getLabel(n.data?._type), properties: n.data?.properties || {} })),
    edges: edges.value.map(e => ({ id: e.id, source: e.source, target: e.target }))
  }
  emit('update:modelValue', data)
}

function onDragStart(event, item) {
  event.dataTransfer.setData('nodeType', item.type)
  event.dataTransfer.setData('nodeLabel', item.label)
  event.dataTransfer.effectAllowed = 'move'
}

function onDrop(event) {
  const type = event.dataTransfer.getData('nodeType')
  const label = event.dataTransfer.getData('nodeLabel')
  if (!type) return
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left - 50
  const y = event.clientY - rect.top - 20
  const id = `${type}_${Date.now()}`
  addNodes([{ id, type: 'default', position: { x, y }, data: { _type: type, text: label }, style: nodeStyle(type), class: 'wf-node' }])
  syncData()
}

function onNodeClick({ node }) {
  selectedNode.value = node
  nodeConfig.value = {
    name: node.data?.text || getLabel(node.data?._type),
    typeLabel: getLabel(node.data?._type),
    color: getColor(node.data?._type),
    approval_type: node.data?.properties?.approval_type || 'single',
    assignee_type: node.data?.properties?.assignee_type || 'specified',
    capability_code: node.data?.properties?.capability_code || ''
  }
}

function onPaneClick() { selectedNode.value = null }

function onConnect(params) {
  edges.value = [...edges.value, { id: `e${params.source}-${params.target}`, source: params.source, target: params.target, type: 'smoothstep', animated: true, style: { stroke: '#1677ff', strokeWidth: 2 } }]
  syncData()
}

function saveConfig() {
  if (!selectedNode.value) return
  const node = nodes.value.find(n => n.id === selectedNode.value.id)
  if (node) {
    node.data = { ...node.data, text: nodeConfig.value.name, properties: { approval_type: nodeConfig.value.approval_type, assignee_type: nodeConfig.value.assignee_type, capability_code: nodeConfig.value.capability_code } }
  }
  syncData()
  ElMessage.success('已保存')
}

function fitViewAction() { fitView({ padding: 0.2 }) }

function clearAll() {
  ElMessageBox.confirm('确定清空？', '确认', { type: 'warning' }).then(() => {
    nodes.value = [{ id: 'start_1', type: 'default', position: { x: 300, y: 100 }, data: { _type: 'start', text: '开始' }, style: nodeStyle('start'), class: 'wf-node' }]
    edges.value = []
    selectedNode.value = null
    syncData()
  }).catch(() => {})
}

function exportData() {
  const data = { nodes: nodes.value.map(n => ({ id: n.id, type: n.data?._type, position: n.position, text: n.data?.text, properties: n.data?.properties || {} })), edges: edges.value.map(e => ({ id: e.id, source: e.source, target: e.target })) }
  ElMessageBox.alert(JSON.stringify(data, null, 2), '流程 JSON', { confirmButtonText: '复制' })
}

function importData() {
  ElMessageBox.prompt('粘贴 JSON', '导入', { inputType: 'textarea' }).then(({ value }) => {
    try {
      const d = JSON.parse(value)
      nodes.value = (d.nodes || []).map(n => ({ id: n.id, type: 'default', position: n.position, data: { _type: n.type, text: n.text, properties: n.properties || {} }, style: nodeStyle(n.type), class: 'wf-node' }))
      edges.value = (d.edges || []).map((e, i) => ({ id: e.id || `e${i}`, source: e.source, target: e.target, type: 'smoothstep', animated: true, style: { stroke: '#1677ff', strokeWidth: 2 } }))
      syncData()
      ElMessage.success('导入成功')
    } catch (e) { ElMessage.error('JSON 格式错误') }
  }).catch(() => {})
}

initData()

watch(() => props.modelValue, (v) => {
  if (v?.nodes?.length && JSON.stringify(v) !== JSON.stringify({ nodes: nodes.value.map(n => ({ id: n.id, type: n.data?._type, position: n.position })), edges: [] })) {
    initData()
  }
}, { deep: true })
</script>

<style scoped>
.flow-modeler { border: 1px solid #e4e7ed; border-radius: 8px; overflow: hidden; height: 100%; display: flex; flex-direction: column; background: #fff; }
.flow-toolbar { padding: 8px 16px; background: #fafafa; border-bottom: 1px solid #e4e7ed; display: flex; align-items: center; gap: 4px; }
.flow-body { flex: 1; display: flex; overflow: hidden; }
.dnd-panel { width: 150px; border-right: 1px solid #e4e7ed; background: #fafafa; flex-shrink: 0; }
.dnd-title { padding: 10px 12px; font-size: 13px; font-weight: 600; border-bottom: 1px solid #e4e7ed; background: #fff; }
.dnd-list { padding: 8px; }
.dnd-item { display: flex; align-items: center; gap: 8px; padding: 8px; margin-bottom: 4px; border-radius: 6px; cursor: grab; background: #fff; border: 1px solid #eee; transition: all .2s; }
.dnd-item:hover { background: #ecf5ff; border-color: #b3d8ff; }
.dnd-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 14px; flex-shrink: 0; }
.dnd-item span { font-size: 12px; color: #606266; }
.graph-area { flex: 1; overflow: hidden; }
.prop-panel { width: 280px; border-left: 1px solid #e4e7ed; background: #fff; display: flex; flex-direction: column; flex-shrink: 0; }
.panel-header { padding: 10px 14px; font-size: 14px; font-weight: 600; border-bottom: 1px solid #e4e7ed; display: flex; justify-content: space-between; align-items: center; background: #fafafa; }
.panel-body { flex: 1; overflow-y: auto; padding: 14px; }
.flow-modeler :deep(.vue-flow__controls) { box-shadow: 0 1px 4px rgba(0,0,0,.1); border-radius: 4px; }
.flow-modeler :deep(.vue-flow__minimap) { border: 1px solid #e4e7ed; border-radius: 4px; }
.flow-modeler :deep(.vue-flow__node) { border-radius: 8px; }
.flow-modeler :deep(.vue-flow__node.selected) { box-shadow: 0 0 0 3px rgba(22,119,255,.2) !important; }
.flow-modeler :deep(.vue-flow__edge-path) { stroke: #1677ff; stroke-width: 2; }
</style>
