<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TopoEdge } from './types'

const props = defineProps<{
  open: boolean
  edge: TopoEdge | null
  sourceName?: string
  targetName?: string
}>()

const emit = defineEmits<{ (e: 'update:open', v: boolean): void }>()

// Mock 关系详情数据
interface RelationDetail {
  // 基础信息
  sourceDomain: string
  sourcePort: number
  targetDomain: string
  targetPort: number
  protocol: string
  relationType: string
  
  // 流量配置
  loadBalance: string
  timeout: number
  retryCount: number
  retryInterval: number
  
  // 安全
  authType: string
  rateLimit: number
  
  // 可观测性
  tracingEnabled: boolean
  metricsEnabled: boolean
  
  // 依赖等级
  criticalLevel: string
  slaTarget: string
  
  // 变更记录
  lastChange: string
  lastOperator: string
}

const mockDetails: Record<string, RelationDetail> = {
  'default': {
    sourceDomain: 'web.frontend.com',
    sourcePort: 443,
    targetDomain: 'api.internal',
    targetPort: 8080,
    protocol: 'HTTPS → HTTP',
    relationType: 'depends_on',
    loadBalance: '轮询',
    timeout: 3000,
    retryCount: 3,
    retryInterval: 100,
    authType: 'mTLS',
    rateLimit: 1000,
    tracingEnabled: true,
    metricsEnabled: true,
    criticalLevel: '核心',
    slaTarget: '99.9%',
    lastChange: '2026-08-06 10:00',
    lastOperator: '张三',
  },
  'database': {
    sourceDomain: 'app.service',
    sourcePort: 8080,
    targetDomain: 'db.rds.internal',
    targetPort: 3306,
    protocol: 'TCP (MySQL)',
    relationType: 'depends_on',
    loadBalance: '主从分离',
    timeout: 5000,
    retryCount: 2,
    retryInterval: 200,
    authType: '数据库账号',
    rateLimit: 500,
    tracingEnabled: false,
    metricsEnabled: true,
    criticalLevel: '核心',
    slaTarget: '99.95%',
    lastChange: '2026-08-05 14:30',
    lastOperator: '李四',
  },
  'cache': {
    sourceDomain: 'app.service',
    sourcePort: 8080,
    targetDomain: 'redis.cache.internal',
    targetPort: 6379,
    protocol: 'TCP (Redis)',
    relationType: 'depends_on',
    loadBalance: '集群模式',
    timeout: 1000,
    retryCount: 1,
    retryInterval: 50,
    authType: '密码认证',
    rateLimit: 10000,
    tracingEnabled: false,
    metricsEnabled: true,
    criticalLevel: '重要',
    slaTarget: '99.9%',
    lastChange: '2026-08-04 09:15',
    lastOperator: '王五',
  },
}

const detail = computed(() => {
  if (!props.edge) return mockDetails['default']
  
  // 根据目标类型返回不同的 mock 数据
  const target = props.edge.target.toLowerCase()
  if (target.includes('database') || target.includes('rds') || target.includes('mysql')) {
    return mockDetails['database']
  }
  if (target.includes('cache') || target.includes('redis')) {
    return mockDetails['cache']
  }
  return mockDetails['default']
})

// 支持的能力列表
const capabilities = [
  { name: '流量监控', supported: true, value: '高', desc: '实时监控服务间调用延迟、错误率、吞吐量' },
  { name: '链路追踪', supported: true, value: '高', desc: '全链路追踪，快速定位问题根因' },
  { name: '熔断降级', supported: false, value: '中', desc: '防止级联故障，保护系统稳定性' },
  { name: '灰度发布', supported: true, value: '高', desc: '按权重分流，支持金丝雀发布' },
  { name: '限流控制', supported: true, value: '中', desc: '保护下游服务不被流量击垮' },
  { name: '自动扩缩', supported: false, value: '高', desc: '根据流量自动调整实例数' },
  { name: '故障注入', supported: false, value: '低', desc: '混沌工程，主动验证系统韧性' },
  { name: '依赖拓扑', supported: true, value: '高', desc: '可视化服务依赖关系，辅助架构决策' },
]

const supportedCount = computed(() => capabilities.filter(c => c.supported).length)
</script>

<template>
  <a-drawer 
    :open="open" 
    :width="520" 
    title="🔗 依赖关系详情" 
    @update:open="emit('update:open', $event)"
  >
    <template v-if="edge">
      <!-- 关系概览 -->
      <div class="relation-overview">
        <div class="service-card source">
          <div class="service-icon">📤</div>
          <div class="service-name">{{ sourceName || edge.source }}</div>
          <div class="service-domain">{{ detail?.sourceDomain }}:{{ detail?.sourcePort }}</div>
        </div>
        <div class="relation-arrow">
          <div class="arrow-line"></div>
          <div class="arrow-label">{{ detail?.protocol }}</div>
          <div class="arrow-type">
            <a-tag :color="edge.strength === 'hard' ? 'purple' : 'default'">
              {{ edge.strength === 'hard' ? '强制依赖' : '软依赖' }}
            </a-tag>
          </div>
        </div>
        <div class="service-card target">
          <div class="service-icon">📥</div>
          <div class="service-name">{{ targetName || edge.target }}</div>
          <div class="service-domain">{{ detail?.targetDomain }}:{{ detail?.targetPort }}</div>
        </div>
      </div>

      <!-- 详细信息 -->
      <a-collapse default-active-key="basic" ghost>
        <!-- 基础信息 -->
        <a-collapse-panel key="basic" header="📋 基础信息">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="关系类型">{{ detail?.relationType }}</a-descriptions-item>
            <a-descriptions-item label="依赖等级">
              <a-tag :color="detail?.criticalLevel === '核心' ? 'red' : detail?.criticalLevel === '重要' ? 'orange' : 'blue'">
                {{ detail?.criticalLevel }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="SLA 目标">{{ detail?.slaTarget }}</a-descriptions-item>
            <a-descriptions-item label="请求协议">{{ detail?.protocol }}</a-descriptions-item>
          </a-descriptions>
        </a-collapse-panel>

        <!-- 流量配置 -->
        <a-collapse-panel key="traffic" header="🔄 流量配置">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="负载均衡">{{ detail?.loadBalance }}</a-descriptions-item>
            <a-descriptions-item label="超时时间">{{ detail?.timeout }}ms</a-descriptions-item>
            <a-descriptions-item label="重试次数">{{ detail?.retryCount }} 次</a-descriptions-item>
            <a-descriptions-item label="重试间隔">{{ detail?.retryInterval }}ms</a-descriptions-item>
          </a-descriptions>
        </a-collapse-panel>

        <!-- 安全配置 -->
        <a-collapse-panel key="security" header="🔒 安全配置">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="认证方式">{{ detail?.authType }}</a-descriptions-item>
            <a-descriptions-item label="限流阈值">{{ detail?.rateLimit }} QPS</a-descriptions-item>
          </a-descriptions>
        </a-collapse-panel>

        <!-- 可观测性 -->
        <a-collapse-panel key="observe" header="📊 可观测性">
          <a-descriptions :column="2" size="small" bordered>
            <a-descriptions-item label="链路追踪">
              <a-badge :status="detail?.tracingEnabled ? 'success' : 'default'" :text="detail?.tracingEnabled ? '已启用' : '未启用'" />
            </a-descriptions-item>
            <a-descriptions-item label="指标采集">
              <a-badge :status="detail?.metricsEnabled ? 'success' : 'default'" :text="detail?.metricsEnabled ? '已启用' : '未启用'" />
            </a-descriptions-item>
          </a-descriptions>
        </a-collapse-panel>

        <!-- 变更记录 -->
        <a-collapse-panel key="history" header="📝 最近变更">
          <div class="change-record" v-if="detail">
            <a-tag color="blue">{{ detail.lastChange }}</a-tag>
            <span>{{ detail.lastOperator }} 修改了配置</span>
          </div>
        </a-collapse-panel>
      </a-collapse>

      <!-- 系统能力评估 -->
      <div class="capabilities-section">
        <div class="section-header">
          <span class="section-title">🎯 系统能力评估</span>
          <a-tag color="green">{{ supportedCount }}/{{ capabilities.length }} 已支持</a-tag>
        </div>
        <div class="capabilities-grid">
          <div v-for="cap in capabilities" :key="cap.name" class="capability-item" :class="{ supported: cap.supported }">
            <div class="cap-header">
              <span class="cap-status">{{ cap.supported ? '✅' : '⬜' }}</span>
              <span class="cap-name">{{ cap.name }}</span>
              <a-tag :color="cap.value === '高' ? 'red' : cap.value === '中' ? 'orange' : 'blue'" size="small">
                {{ cap.value }}价值
              </a-tag>
            </div>
            <div class="cap-desc">{{ cap.desc }}</div>
          </div>
        </div>
      </div>

      <!-- 当前状态 -->
      <a-alert 
        type="info" 
        show-icon 
        style="margin-top: 16px"
      >
        <template #message>
          <span>📌 以上为 Mock 数据，实际部署后将对接真实配置</span>
        </template>
        <template #description>
          <span>当前展示的是理想状态下的关系详情能力，用于评估系统价值。后续可根据实际后端能力进行调整。</span>
        </template>
      </a-alert>
    </template>
  </a-drawer>
</template>

<style scoped>
.relation-overview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  background: #F8FAFC;
  border-radius: 12px;
  margin-bottom: 20px;
}

.service-card {
  flex: 1;
  text-align: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.service-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.service-name {
  font-size: 14px;
  font-weight: 600;
  color: #1E293B;
  margin-bottom: 4px;
}

.service-domain {
  font-size: 12px;
  color: #64748B;
  font-family: monospace;
}

.relation-arrow {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 100px;
}

.arrow-line {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #3B82F6, #8B5CF6);
  position: relative;
}

.arrow-line::after {
  content: '→';
  position: absolute;
  right: -8px;
  top: -8px;
  color: #8B5CF6;
  font-size: 16px;
}

.arrow-label {
  font-size: 11px;
  color: #64748B;
}

.capabilities-section {
  margin-top: 20px;
  padding: 16px;
  background: #F0FDF4;
  border-radius: 12px;
  border: 1px solid #BBF7D0;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #166534;
}

.capabilities-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.capability-item {
  padding: 10px 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #E2E8F0;
}

.capability-item.supported {
  border-color: #86EFAC;
  background: #F0FFF4;
}

.cap-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.cap-status {
  font-size: 14px;
}

.cap-name {
  font-size: 13px;
  font-weight: 500;
  color: #1E293B;
}

.cap-desc {
  font-size: 12px;
  color: #64748B;
  padding-left: 22px;
}

.change-record {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #64748B;
}
</style>
