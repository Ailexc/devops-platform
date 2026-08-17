<template>
  <div class="flow-node-status">
    <div v-if="status.instance_no" class="instance-meta">
      <span>单号：{{ status.instance_no }}</span>
      <span class="meta-sep">｜</span>
      <span>流程状态：{{ status.status_display }}</span>
    </div>

    <el-empty v-if="!status.nodes?.length" description="暂无流程节点信息" :image-size="60" />

    <!-- 左右两栏：左侧节点链路 / 右侧节点详情 -->
    <div v-else class="fns-body">
      <!-- 左：节点链路 -->
      <div class="fns-chain">
        <div
          v-for="(node, idx) in status.nodes"
          :key="node.key"
          class="chain-item"
          :class="[
            'chain-item--' + node.status,
            { 'is-active': currentNode && currentNode.key === node.key }
          ]"
          @click="selectNode(node)"
        >
          <div class="chain-rail">
            <div class="chain-dot"><span class="chain-dot__inner"></span></div>
            <div v-if="idx < status.nodes.length - 1" class="chain-line"></div>
          </div>
          <div class="chain-content">
            <div class="chain-top">
              <span class="chain-name">{{ node.name }}</span>
              <span class="chain-type">{{ node.type_label }}</span>
            </div>
            <div class="chain-sub">{{ statusText(node) }}</div>
            <div v-if="nodeHandler(node)" class="chain-handler">
              <el-icon><User /></el-icon> {{ nodeHandler(node) }}
            </div>
            <el-button
              v-if="node.status === 'abnormal'"
              type="danger"
              size="small"
              class="chain-fault-btn"
              @click.stop="openSupportCard"
            >
              进入故障支持群
            </el-button>
          </div>
        </div>
      </div>

      <!-- 右：节点详情 -->
      <div class="fns-detail">
        <template v-if="currentNode">
          <div class="detail-head">
            <div class="detail-head__left">
              <span class="detail-head__name">{{ currentNode.name }}</span>
              <el-tag size="small" effect="plain">{{ currentNode.type_label }}</el-tag>
            </div>
            <el-tag size="small" :type="stateTag(currentNode.status)">{{ statusText(currentNode) }}</el-tag>
          </div>

          <!-- 节点信息 / 任务配置 -->
          <div class="detail-card">
            <div class="detail-card__title">节点信息 · 任务配置</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">节点类型</span>
                <span class="info-value">{{ currentNode.type_label }}</span>
              </div>
              <template v-if="currentNode.type === 'approve'">
                <div class="info-item">
                  <span class="info-label">审批方式</span>
                  <span class="info-value">{{ detail.approval_type?.label || '-' }}</span>
                </div>
                <div class="info-item info-item--full">
                  <span class="info-label">审批人</span>
                  <span class="info-value">{{ detail.approvers || '-' }}</span>
                </div>
              </template>
              <template v-else-if="currentNode.type === 'handle'">
                <div class="info-item">
                  <span class="info-label">办理方式</span>
                  <span class="info-value">{{ detail.mode?.label || '-' }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">执行模式</span>
                  <span class="info-value">{{ detail.execution_mode?.label || '-' }}</span>
                </div>
                <div v-if="nodeIsAsync !== null" class="info-item info-item--full">
                  <span class="info-label">执行方式</span>
                  <div class="channel-tags">
                    <span class="channel-tag" :class="{ 'is-used': nodeIsAsync === false }">
                      <el-icon v-if="nodeIsAsync === false"><Check /></el-icon>
                      同步（阻塞等待执行结果）
                    </span>
                    <span class="channel-tag" :class="{ 'is-used': nodeIsAsync === true }">
                      <el-icon v-if="nodeIsAsync === true"><Check /></el-icon>
                      异步（提交任务队列即返回，结果经队列消息/回调回写）
                    </span>
                  </div>
                  <span class="info-hint">节点内任一动作异步即整体异步；真实场景异步任务状态由队列/Webhook 回调刷新</span>
                </div>
                <div class="info-item">
                  <span class="info-label">动作数</span>
                  <span class="info-value">{{ detail.action_count || 0 }}</span>
                </div>
                <div class="info-item info-item--full">
                  <span class="info-label">办理人</span>
                  <span class="info-value">{{ detail.handlers || '-' }}</span>
                </div>
                <div v-if="detail.actions?.length" class="info-item info-item--full">
                  <span class="info-label">配置动作</span>
                  <div class="cfg-actions">
                    <div v-for="a in detail.actions" :key="a.key" class="cfg-action">
                      <span class="cfg-action__name">{{ a.name }}</span>
                      <span class="cfg-action__cap">{{ a.capability }}</span>
                    </div>
                  </div>
                </div>
              </template>
              <template v-else-if="currentNode.type === 'cc'">
                <div class="info-item info-item--full">
                  <span class="info-label">抄送人</span>
                  <span class="info-value">{{ detail.ccs || '-' }}</span>
                </div>
              </template>
              <!-- 多渠道审批 / 办理（演示模拟） -->
              <div v-if="currentNode.channels?.length" class="info-item info-item--full">
                <span class="info-label">{{ currentNode.type === 'approve' ? '审批渠道' : '办理渠道' }}</span>
                <div class="channel-tags">
                  <span
                    v-for="c in currentNode.channels"
                    :key="c.code"
                    class="channel-tag"
                    :class="{ 'is-used': c.code === currentNode.channel }"
                  >
                    <el-icon v-if="c.code === currentNode.channel"><Check /></el-icon>
                    {{ c.label }}{{ c.code === currentNode.channel ? '（本次）' : '' }}
                  </span>
                </div>
                <span class="info-hint">真实场景支持 Web / Lark 飞书多渠道审批，本环境为模拟展示</span>
              </div>
              <!-- 审批/办理备注（演示模拟）已并入下方「意见·备注」卡片 -->
              <div class="info-item">
                <span class="info-label">节点状态</span>
                <span class="info-value">{{ statusText(currentNode) }}</span>
              </div>
              <div v-if="currentNode.proxy_name" class="info-item">
                <span class="info-label">实际办理人</span>
                <span class="info-value">{{ currentNode.proxy_name }}</span>
              </div>
            </div>
          </div>

          <!-- 审批意见 / 办理备注 -->
          <div v-if="currentNode.opinion || currentNode.remark" class="detail-card">
            <div class="detail-card__title">{{ currentNode.type === 'approve' ? '审批意见 · 备注' : '办理备注' }}</div>
            <div v-if="currentNode.opinion" class="opinion-block">
              <span class="opinion-label">意见</span>
              <div class="opinion-text">{{ currentNode.opinion }}</div>
            </div>
            <div v-if="currentNode.remark" class="opinion-block">
              <span class="opinion-label">备注</span>
              <div class="opinion-text">{{ currentNode.remark }}</div>
            </div>
            <span class="info-hint">演示数据：真实场景中审批/办理人可在处理时填写意见与备注</span>
          </div>

          <!-- 任务执行 -->
          <div class="detail-card">
            <div class="detail-card__title">任务执行</div>
            <el-alert
              v-if="currentNode.error"
              type="error"
              :closable="false"
              show-icon
              title="节点异常"
              :description="currentNode.error"
            />
            <template v-if="currentNode.actions?.length">
              <div v-for="action in currentNode.actions" :key="action.action_key || action.capability_code" class="exec-block">
                <div class="exec-head">
                  <span class="exec-name">{{ action.action_name || action.capability_code }}</span>
                  <el-tag v-if="action.sync !== undefined" :type="action.sync ? 'info' : 'warning'" size="small">
                    {{ action.sync ? '同步' : '异步' }}
                  </el-tag>
                  <el-tag :type="statusTag(action.status)" size="small">{{ actionStatusLabel(action.status) }}</el-tag>
                </div>
                <div v-if="action.error_message" class="exec-error">{{ action.error_message }}</div>
                <div v-if="hasData(action.input_data)" class="exec-io">
                  <span class="exec-io__label">入参</span>
                  <pre class="exec-io__json">{{ json(action.input_data) }}</pre>
                </div>
                <div v-if="hasData(action.output_data)" class="exec-io">
                  <span class="exec-io__label">出参</span>
                  <pre class="exec-io__json">{{ json(action.output_data) }}</pre>
                </div>
              </div>
            </template>
            <div v-else class="detail-empty">该节点无可执行动作（人工审批 / 发起 / 结束）</div>
          </div>

          <!-- 流程日志 -->
          <div class="detail-card">
            <div class="detail-card__title">流程日志</div>
            <div v-if="allLogs.length" class="log-timeline">
              <div v-for="(log, i) in allLogs" :key="i" class="log-line">
                <div class="log-marker" :class="'log-marker--' + log.level"></div>
                <div class="log-body">
                  <div class="log-top">
                    <span class="log-time">{{ formatLogTs(log.ts) }}</span>
                    <span class="log-level" :class="'log-level--' + log.level">{{ log.level }}</span>
                    <span v-if="log.action" class="log-action">{{ log.action }}</span>
                  </div>
                  <div class="log-msg">{{ log.message }}</div>
                </div>
              </div>
            </div>
            <div v-else class="detail-empty">该节点暂无执行日志</div>
          </div>
        </template>
        <el-empty v-else description="点击左侧节点查看详情" :image-size="60" />
      </div>
    </div>

    <!-- 故障支持群（demo 卡片：说明真实业务机制） -->
    <el-dialog v-model="supportVisible" title="故障支持群（演示说明）" width="540px">
      <div class="support-card">
        <p class="support-intro">真实业务中，节点异常时系统会自动创建飞书故障支持群，并支持双向跳转：</p>
        <ul class="support-list">
          <li>流程节点上的「进入故障支持群」按钮 → 点击跳转到飞书群，群内可查看异常详情与执行日志；</li>
          <li>飞书群机器人消息带「查看工单」按钮 → 点击跳回本申请页面；</li>
          <li>群内自动通知申请人与相关办理人，共同排查解决。</li>
        </ul>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          title="本演示环境未接入真实飞书，此按钮仅展示上述真实业务机制"
        />
      </div>
      <template #footer>
        <el-button type="primary" @click="supportVisible = false">我知道了</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { User, Check } from '@element-plus/icons-vue'
import { getInstanceFlowStatus } from '@/api/modules/process'

const props = defineProps({
  instanceId: { type: [String, Number], required: true }
})

const status = ref({ nodes: [] })
const currentNode = ref(null)
const supportVisible = ref(false)

const detail = computed(() => currentNode.value?.detail || {})

// 节点执行方式：任一动作异步即整体异步（null=无动作/未知）
const nodeIsAsync = computed(() => {
  const acts = currentNode.value?.actions || []
  if (!acts.length) return null
  return acts.some(a => a.sync === false)
})

const statusText = (node) => {
  const map = {
    pending: '等待执行',
    claimed: '待处理',
    running: '执行中',
    abnormal: '异常（待人工处理）',
    completed: '已完成',
    rejected: '已驳回',
    not_executed: '未执行（流程已终止）',
    skipped: '已跳过',
    cancelled: '已取消'
  }
  if (node.status === 'abnormal' && node.proxy_name) {
    return `异常，代理办理人：${node.proxy_name}`
  }
  if (node.status === 'running' && node.proxy_name) {
    return `${node.mode === 'confirm' ? '确认已通过' : '自动执行中'}，办理人：${node.proxy_name}`
  }
  if (node.status === 'pending' && node.mode === 'confirm') {
    return '待确认（办理人确认后执行动作）'
  }
  return map[node.status] || node.status || ''
}

const stateTag = (s) => ({
  completed: 'success',
  abnormal: 'danger',
  rejected: 'danger',
  running: 'primary',
  claimed: 'warning',
  pending: 'info',
  not_executed: 'info',
  skipped: 'info',
  cancelled: 'info'
})[s] || 'info'

const statusTag = (s) => ({
  succeeded: 'success',
  failed: 'danger',
  running: 'primary',
  queued: 'info'
})[s] || 'info'

const actionStatusLabel = (s) => ({
  succeeded: '成功',
  failed: '失败',
  running: '执行中',
  queued: '排队中'
})[s] || s || ''

// 左侧链路展示的办理人：实际办理人 → 配置审批人/办理人/抄送人
const nodeHandler = (node) => {
  if (node.proxy_name) return node.proxy_name
  const d = node.detail || {}
  return d.approvers || d.handlers || d.ccs || ''
}

const selectNode = (node) => {
  currentNode.value = node
}

const hasData = (obj) => obj && typeof obj === 'object' && Object.keys(obj).length > 0
const json = (obj) => JSON.stringify(obj, null, 2)

const formatLogTs = (ts) => {
  if (!ts) return ''
  const s = String(ts)
  return s.length >= 19 ? `${s.slice(0, 10)} ${s.slice(11, 19)}` : s
}

// 汇总所有动作日志为时间线
const allLogs = computed(() => {
  const logs = []
  ;(currentNode.value?.actions || []).forEach(a => {
    ;(a.logs || []).forEach(l => {
      logs.push({ ts: l.ts, level: l.level, message: l.message, action: a.action_name })
    })
  })
  return logs
})

const fetchStatus = async () => {
  try {
    const response = await getInstanceFlowStatus(props.instanceId)
    status.value = response?.data ?? response
    const nodes = status.value?.nodes || []
    if (nodes.length) {
      // 默认选中第一个（多为发起节点，或第一个有动作的节点）
      currentNode.value = nodes.find(n => n.actions?.length) || nodes[0]
    }
  } catch (error) {
    console.error('获取流程状态失败:', error)
  }
}

const openSupportCard = () => {
  supportVisible.value = true
}

onMounted(fetchStatus)

defineExpose({ refresh: fetchStatus })
</script>

<style scoped lang="scss">
.flow-node-status {
  .instance-meta {
    font-size: 13px;
    color: #86909c;
    margin-bottom: 16px;

    .meta-sep {
      margin: 0 6px;
    }
  }

  .fns-body {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }

  /* ===== 左：节点链路 ===== */
  .fns-chain {
    width: 340px;
    flex-shrink: 0;
    border: 1px solid #e5e6eb;
    border-radius: 10px;
    background: #fff;
    padding: 12px 10px;
    max-height: 640px;
    overflow: auto;
  }

  .chain-item {
    display: flex;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: background .15s;

    &:hover {
      background: #f7f8fa;
    }

    &.is-active {
      background: #ecf5ff;
      box-shadow: inset 3px 0 0 #409eff;
    }
  }

  .chain-rail {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex-shrink: 0;
    width: 18px;
  }

  .chain-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    background: #fff;
    border: 2px solid #c9cdd4;

    &__inner {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: transparent;
    }
  }

  .chain-item--completed .chain-dot {
    border-color: #00b42a;

    .chain-dot__inner { background: #00b42a; }
  }

  .chain-item--running .chain-dot,
  .chain-item--claimed .chain-dot {
    border-color: #409eff;

    .chain-dot__inner { background: #409eff; }
  }

  .chain-item--abnormal .chain-dot {
    border-color: #f53f3f;

    .chain-dot__inner { background: #f53f3f; }
  }

  .chain-item--rejected .chain-dot {
    border-color: #ff7d00;

    .chain-dot__inner { background: #ff7d00; }
  }

  .chain-item--not_executed .chain-dot {
    border-style: dashed;
    border-color: #c9cdd4;

    .chain-dot__inner { background: transparent; }
  }

  .chain-item--pending .chain-dot .chain-dot__inner { background: #c9cdd4; }

  .chain-line {
    flex: 1;
    width: 2px;
    min-height: 22px;
    background: #e5e6eb;
    margin-top: 2px;
  }

  .chain-content {
    flex: 1;
    min-width: 0;
    padding-bottom: 14px;
  }

  .chain-top {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
  }

  .chain-name {
    font-size: 14px;
    font-weight: 600;
    color: #1d2129;
  }

  .chain-type {
    font-size: 11px;
    color: #86909c;
    background: #f2f3f5;
    border-radius: 4px;
    padding: 0 6px;
  }

  .chain-sub {
    font-size: 12px;
    color: #86909c;
    margin-top: 2px;
  }

  .chain-handler {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #722ed1;
    background: #f4f0ff;
    border-radius: 4px;
    padding: 1px 6px;
    margin-top: 6px;
    width: fit-content;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chain-fault-btn {
    margin-top: 6px;
  }

  /* ===== 右：节点详情 ===== */
  .fns-detail {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .detail-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #fff;
    border: 1px solid #e5e6eb;
    border-radius: 10px;
    padding: 14px 18px;

    &__left {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    &__name {
      font-size: 16px;
      font-weight: 600;
      color: #1d2129;
    }
  }

  .detail-card {
    background: #fff;
    border: 1px solid #e5e6eb;
    border-radius: 10px;
    padding: 14px 18px;

    &__title {
      font-size: 13px;
      font-weight: 600;
      color: #1d2129;
      margin-bottom: 12px;
      padding-left: 8px;
      border-left: 3px solid #165dff;
      line-height: 1.2;
    }
  }

  .info-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px 24px;
  }

  .info-item {
    display: flex;
    flex-direction: column;
    gap: 3px;

    &--full {
      grid-column: 1 / -1;
    }
  }

  .info-label {
    font-size: 12px;
    color: #86909c;
  }

  .info-value {
    font-size: 13px;
    color: #1d2129;
    word-break: break-all;
  }

  .cfg-actions {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .cfg-action {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f7f8fa;
    border-radius: 6px;
    padding: 6px 10px;

    &__name {
      font-size: 13px;
      color: #1d2129;
      font-weight: 500;
    }

    &__cap {
      font-size: 12px;
      color: #165dff;
      font-family: ui-monospace, monospace;
    }
  }

  .exec-block {
    border: 1px solid #f2f3f5;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    background: #fbfbfc;

    &:last-child { margin-bottom: 0; }
  }

  .exec-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .exec-name {
    font-size: 13px;
    font-weight: 600;
    color: #1d2129;
  }

  .exec-error {
    margin-top: 8px;
    font-size: 12px;
    color: #f53f3f;
    background: #ffece8;
    border-radius: 6px;
    padding: 6px 10px;
  }

  .exec-io {
    margin-top: 8px;
    display: flex;
    gap: 8px;
    align-items: flex-start;

    &__label {
      font-size: 12px;
      color: #86909c;
      flex-shrink: 0;
      line-height: 20px;
    }

    &__json {
      flex: 1;
      margin: 0;
      font-size: 11px;
      color: #4e5969;
      background: #fff;
      border: 1px solid #f2f3f5;
      border-radius: 6px;
      padding: 8px;
      overflow: auto;
      line-height: 1.5;
      white-space: pre-wrap;
      word-break: break-all;
    }
  }

  .log-timeline {
    display: flex;
    flex-direction: column;
  }

  .log-line {
    display: flex;
    gap: 10px;
    padding: 4px 0;
  }

  .log-marker {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-top: 5px;
    flex-shrink: 0;

    &--info { background: #4080ff; }
    &--debug { background: #c9cdd4; }
    &--warn { background: #ff7d00; }
    &--error { background: #f53f3f; }
  }

  .log-body {
    flex: 1;
    min-width: 0;
  }

  .log-top {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .log-time {
    font-size: 11px;
    color: #c9cdd4;
    font-family: ui-monospace, monospace;
  }

  .log-level {
    font-size: 11px;
    font-weight: 600;

    &--info { color: #4080ff; }
    &--debug { color: #86909c; }
    &--warn { color: #ff7d00; }
    &--error { color: #f53f3f; }
  }

  .log-action {
    font-size: 11px;
    color: #722ed1;
    background: #f4f0ff;
    border-radius: 4px;
    padding: 0 6px;
  }

  .log-msg {
    font-size: 12px;
    color: #4e5969;
    line-height: 1.6;
  }

  .detail-empty {
    font-size: 13px;
    color: #c9cdd4;
    padding: 12px 0;
  }

  .info-hint {
    font-size: 11px;
    color: #c9cdd4;
  }

  .channel-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .channel-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #86909c;
    background: #f2f3f5;
    border: 1px solid #e5e6eb;
    border-radius: 14px;
    padding: 3px 10px;

    &.is-used {
      color: #165dff;
      background: #e8f3ff;
      border-color: #a0cfff;
      font-weight: 600;
    }
  }

  .opinion-block {
    display: flex;
    gap: 8px;
    align-items: flex-start;
    margin-bottom: 8px;

    &:last-child { margin-bottom: 0; }
  }

  .opinion-label {
    flex-shrink: 0;
    font-size: 12px;
    color: #86909c;
    background: #f2f3f5;
    border-radius: 4px;
    padding: 2px 8px;
    line-height: 18px;
  }

  .opinion-text {
    flex: 1;
    min-width: 0;
    font-size: 13px;
    color: #4e5969;
    background: #f7f8fa;
    border-radius: 6px;
    padding: 6px 10px;
    line-height: 1.6;
    word-break: break-all;
  }

  .support-card {
    .support-intro {
      margin: 0 0 10px;
      color: #4e5969;
      font-size: 14px;
    }

    .support-list {
      margin: 0 0 14px;
      padding-left: 20px;
      color: #4e5969;
      font-size: 13px;
      line-height: 2;
    }
  }
}
</style>
