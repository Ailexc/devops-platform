<template>
  <div class="flow-canvas-sim">
    <!-- 顶部工具栏 -->
    <div class="canvas-toolbar">
      <div class="toolbar-left">
        <span class="flow-name">服务器申请流程</span>
        <span class="flow-status">草稿</span>
      </div>
      <div class="toolbar-center">
        <span class="tool-btn active">🖱️ 选择</span>
        <span class="tool-btn">✏️ 连线</span>
        <span class="tool-btn">🗑️ 删除</span>
      </div>
      <div class="toolbar-right">
        <span class="zoom-info">100%</span>
      </div>
    </div>

    <!-- 画布主体 -->
    <div class="canvas-body">
      <!-- 左侧节点面板 -->
      <div class="node-palette">
        <div class="palette-section">
          <div class="palette-title">基础节点</div>
          <div class="palette-node" v-for="n in baseNodes" :key="n.name">
            <span class="node-icon" :style="{ background: n.color }">{{ n.icon }}</span>
            <span class="node-name">{{ n.name }}</span>
          </div>
        </div>
        <div class="palette-section">
          <div class="palette-title">逻辑节点</div>
          <div class="palette-node" v-for="n in logicNodes" :key="n.name">
            <span class="node-icon" :style="{ background: n.color }">{{ n.icon }}</span>
            <span class="node-name">{{ n.name }}</span>
          </div>
        </div>
      </div>

      <!-- 画布 -->
      <div class="canvas-area">
        <svg class="flow-lines" viewBox="0 0 800 400">
          <!-- 连线 -->
          <path d="M 120 60 L 250 60" stroke="#dcdfe6" stroke-width="2" marker-end="url(#arrow)" />
          <path d="M 350 60 L 480 60" stroke="#dcdfe6" stroke-width="2" marker-end="url(#arrow)" />
          <path d="M 580 60 L 680 60" stroke="#dcdfe6" stroke-width="2" marker-end="url(#arrow)" />
          <path d="M 350 60 L 480 180" stroke="#e6a23c" stroke-width="2" stroke-dasharray="6,3" marker-end="url(#arrow)" />
          <path d="M 580 180 L 680 60" stroke="#e6a23c" stroke-width="2" stroke-dasharray="6,3" marker-end="url(#arrow)" />
          <defs>
            <marker id="arrow" markerWidth="8" markerHeight="8" refX="8" refY="4" orient="auto">
              <path d="M 0 0 L 8 4 L 0 8 Z" fill="#dcdfe6" />
            </marker>
          </defs>
        </svg>

        <!-- 节点 -->
        <div class="flow-node start" style="left: 40px; top: 40px;">
          <div class="node-body start-node">发起申请</div>
        </div>
        <div class="flow-node" :class="{ active: activeNode === 'approval' }" style="left: 220px; top: 40px;" @click="activeNode = 'approval'">
          <div class="node-body approval-node">
            <div class="node-badge">👤</div>
            <div class="node-info">
              <div class="node-label">运维审批</div>
              <div class="node-sub">指定审批人：小李</div>
            </div>
          </div>
        </div>
        <div class="flow-node" :class="{ active: activeNode === 'transact' }" style="left: 450px; top: 40px;" @click="activeNode = 'transact'">
          <div class="node-body transact-node">
            <div class="node-badge">⚡</div>
            <div class="node-info">
              <div class="node-label">自动开通</div>
              <div class="node-sub">绑定能力：CMDB 创建主机</div>
            </div>
          </div>
        </div>
        <div class="flow-node" :class="{ active: activeNode === 'condition' }" style="left: 450px; top: 160px;" @click="activeNode = 'condition'">
          <div class="node-body condition-node">
            <div class="node-badge">🔀</div>
            <div class="node-info">
              <div class="node-label">条件分支</div>
              <div class="node-sub">金额 > 10000 → 财务审批</div>
            </div>
          </div>
        </div>
        <div class="flow-node end" style="left: 660px; top: 40px;">
          <div class="node-body end-node">结束</div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="property-panel" v-if="activeNode">
        <div class="panel-header">
          <span class="panel-title">节点属性</span>
          <span class="panel-close" @click="activeNode = null">✕</span>
        </div>
        <div class="panel-body" v-if="activeNode === 'approval'">
          <div class="prop-group">
            <div class="prop-label">节点名称</div>
            <div class="prop-value">运维审批</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">节点类型</div>
            <div class="prop-value"><span class="type-tag approval">人工审批</span></div>
          </div>
          <div class="prop-group">
            <div class="prop-label">审批人</div>
            <div class="prop-value">指定人员：小李</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">审批方式</div>
            <div class="prop-value">或签（一人通过即可）</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">意见设置</div>
            <div class="prop-value">必填</div>
          </div>
        </div>
        <div class="panel-body" v-if="activeNode === 'transact'">
          <div class="prop-group">
            <div class="prop-label">节点名称</div>
            <div class="prop-value">自动开通</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">节点类型</div>
            <div class="prop-value"><span class="type-tag transact">自动办理</span></div>
          </div>
          <div class="prop-group">
            <div class="prop-label">绑定能力</div>
            <div class="prop-value">CMDB 创建主机</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">执行模式</div>
            <div class="prop-value">HTTP 模式</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">代理办理人</div>
            <div class="prop-value">小李（审批人代理）</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">自动通过</div>
            <div class="prop-value"><span class="switch-on">●</span> 审批通过后自动执行</div>
          </div>
        </div>
        <div class="panel-body" v-if="activeNode === 'condition'">
          <div class="prop-group">
            <div class="prop-label">节点名称</div>
            <div class="prop-value">条件分支</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">条件表达式</div>
            <div class="prop-value code">amount > 10000</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">满足条件</div>
            <div class="prop-value">→ 财务审批</div>
          </div>
          <div class="prop-group">
            <div class="prop-label">不满足条件</div>
            <div class="prop-value">→ 自动开通</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{ focus?: string }>()

const activeNode = ref('transact')

const baseNodes = [
  { icon: '▶️', name: '开始', color: '#67c23a' },
  { icon: '👤', name: '人工审批', color: '#409eff' },
  { icon: '⚡', name: '自动办理', color: '#e6a23c' },
  { icon: '📝', name: '抄送通知', color: '#909399' },
  { icon: '⏹️', name: '结束', color: '#f56c6c' },
]
const logicNodes = [
  { icon: '🔀', name: '条件分支', color: '#e6a23c' },
  { icon: '⊕', name: '并行网关', color: '#67c23a' },
]
</script>

<style scoped lang="scss">
.flow-canvas-sim { width: 100%; height: 100%; display: flex; flex-direction: column; background: #f5f7fa; }

.canvas-toolbar {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #e5e6eb; padding: 8px 16px; flex-shrink: 0;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; }
.flow-name { font-size: 14px; font-weight: 600; color: #1d2129; }
.flow-status { font-size: 11px; padding: 2px 8px; background: #f5f7fa; border-radius: 4px; color: #86909c; }
.toolbar-center { display: flex; gap: 4px; }
.tool-btn { padding: 4px 10px; font-size: 12px; border-radius: 4px; cursor: pointer; color: #4e5969;
  &.active { background: #ecf5ff; color: #409eff; }
  &:hover { background: #f5f7fa; }
}
.toolbar-right { font-size: 12px; color: #86909c; }

.canvas-body { flex: 1; display: flex; overflow: hidden; }

.node-palette {
  width: 140px; background: #fff; border-right: 1px solid #e5e6eb; padding: 12px; flex-shrink: 0;
}
.palette-section { margin-bottom: 16px; }
.palette-title { font-size: 11px; font-weight: 600; color: #86909c; margin-bottom: 8px; text-transform: uppercase; }
.palette-node {
  display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px;
  cursor: grab; font-size: 12px; color: #4e5969; &:hover { background: #f5f7fa; }
}
.node-icon { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #fff; }
.node-name { font-size: 12px; }

.canvas-area {
  flex: 1; position: relative; overflow: hidden; background: #fff;
  background-image: radial-gradient(circle, #e5e6eb 1px, transparent 1px);
  background-size: 20px 20px;
}
.flow-lines { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.flow-node { position: absolute; cursor: pointer; z-index: 2;
  &:hover .node-body { border-color: #409eff; }
  &.active .node-body { border-color: #409eff; box-shadow: 0 0 0 3px rgba(64,158,255,0.15); }
}
.node-body {
  display: flex; align-items: center; gap: 8px; padding: 10px 16px;
  background: #fff; border: 2px solid #e5e6eb; border-radius: 10px;
  transition: all 0.2s; min-width: 150px;
}
.start-node, .end-node { justify-content: center; min-width: 80px; font-size: 13px; font-weight: 500; }
.start-node { border-color: #67c23a; color: #67c23a; background: #f0f9eb; }
.end-node { border-color: #f56c6c; color: #f56c6c; background: #fef0f0; }
.approval-node { border-color: #409eff; }
.transact-node { border-color: #e6a23c; }
.condition-node { border-color: #e6a23c; border-style: dashed; }
.node-badge { font-size: 18px; }
.node-label { font-size: 13px; font-weight: 600; color: #1d2129; }
.node-sub { font-size: 11px; color: #86909c; margin-top: 2px; }

.property-panel {
  width: 240px; background: #fff; border-left: 1px solid #e5e6eb; flex-shrink: 0; display: flex; flex-direction: column;
}
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid #f2f3f5;
}
.panel-title { font-size: 13px; font-weight: 600; color: #1d2129; }
.panel-close { cursor: pointer; color: #c0c4cc; font-size: 14px; &:hover { color: #4e5969; } }
.panel-body { padding: 16px; flex: 1; overflow-y: auto; }
.prop-group { margin-bottom: 14px; }
.prop-label { font-size: 11px; color: #86909c; margin-bottom: 4px; }
.prop-value { font-size: 13px; color: #1d2129; }
.prop-value.code { font-family: monospace; background: #f5f7fa; padding: 4px 8px; border-radius: 4px; font-size: 12px; }
.type-tag { padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }
.type-tag.approval { background: #ecf5ff; color: #409eff; }
.type-tag.transact { background: #fdf6ec; color: #e6a23c; }
.switch-on { color: #67c23a; }
</style>
