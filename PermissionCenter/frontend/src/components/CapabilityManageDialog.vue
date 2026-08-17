<template>
  <el-dialog v-model="visible" title="能力包管理" width="580px" :close-on-click-modal="false">
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <span>加载中...</span>
    </div>
    <div v-else-if="error" class="error-state">
      <el-icon :size="24"><WarningFilled /></el-icon>
      <span>{{ error }}</span>
    </div>
    <div v-else class="manage-content">
      <div class="cap-header">
        <div class="cap-icon">{{ iconOf(capName) }}</div>
        <div class="cap-info">
          <div class="cap-name">{{ capName }}</div>
          <div class="cap-desc">共 {{ presets.length }} 个预设</div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">📋 已具备的预设</div>
        <div v-if="grantedPresets.length === 0" class="empty-tip">暂无已授权的预设</div>
        <div v-for="preset in grantedPresets" :key="preset.id" class="preset-card granted">
          <div class="preset-header">
            <span class="preset-status granted">✅ 已授权</span>
            <span class="preset-name">{{ preset.name }}</span>
          </div>
          <div class="preset-interfaces">
            <span v-for="iface in preset.interfaces" :key="iface" class="iface-tag">{{ iface }}</span>
          </div>
          <div class="preset-grant-info">
            <span class="grant-meta">
              {{ DIM[preset.grant?.grantee_type] || preset.grant?.grantee_type }} · {{ preset.grant?.grantee_name }}
            </span>
            <span class="grant-time">{{ preset.grant?.created_at }}</span>
          </div>
          <div class="preset-actions">
            <el-button type="danger" size="small" plain @click="revokePreset(preset)">
              退还该预设
            </el-button>
          </div>
        </div>
      </div>

      <div class="section">
        <div class="section-title">📦 可申请的预设</div>
        <div v-if="availablePresets.length === 0" class="empty-tip">暂无可申请的预设</div>
        <div v-for="preset in availablePresets" :key="preset.id" class="preset-card available">
          <div class="preset-header">
            <span class="preset-status available">⬜ 未授权</span>
            <span class="preset-name">{{ preset.name }}</span>
          </div>
          <div class="preset-interfaces">
            <span v-for="iface in preset.interfaces" :key="iface" class="iface-tag">{{ iface }}</span>
          </div>
          <div class="preset-actions">
            <el-button type="primary" size="small" @click="applyPreset(preset)">
              申请该预设
            </el-button>
          </div>
        </div>
      </div>

      <div class="footer-actions">
        <el-button type="danger" plain @click="revokeAll" :disabled="grantedPresets.length === 0">
          退还整个能力包
        </el-button>
        <el-button @click="visible = false">关闭</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import { api } from '../api/client'

const props = defineProps<{
  capabilityId: number
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
}>()

const visible = defineModel<boolean>({ default: false })
const loading = ref(false)
const error = ref('')
const capName = ref('')
const presets = ref<any[]>([])

const DIM: Record<string, string> = {
  user: '个人',
  org: '组织',
  group: '组',
  app: '应用',
}

const grantedPresets = computed(() => presets.value.filter(p => p.granted))
const availablePresets = computed(() => presets.value.filter(p => !p.granted && p.status === 'published'))

function iconOf(name: string) {
  if (!name) return '📦'
  if (name.includes('权限') || name.includes('开通')) return '🔑'
  if (name.includes('管理')) return '⚙️'
  if (name.includes('配置')) return '🛠️'
  return '📦'
}

async function loadData() {
  if (!props.capabilityId) return
  loading.value = true
  error.value = ''
  try {
    const data = await api.meCapabilityPresets(props.capabilityId)
    capName.value = data.capability_name
    presets.value = data.presets || []
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

watch(visible, (v) => {
  if (v && props.capabilityId) {
    loadData()
  }
})

async function revokePreset(preset: any) {
  try {
    await ElMessageBox.confirm(
      `确定要退还预设「${preset.name}」吗？这将发起一个退还申请。`,
      '确认退还',
      { type: 'warning', confirmButtonText: '确认退还', cancelButtonText: '取消' }
    )
    await api.meRevokePreset(props.capabilityId, preset.id, { reason: '用户主动退还' })
    ElMessage.success('退还申请已提交')
    loadData()
    emit('refresh')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '退还失败')
    }
  }
}

async function revokeAll() {
  try {
    await ElMessageBox.confirm(
      `确定要退还整个能力包「${capName.value}」吗？这将退还所有已授权的预设。`,
      '确认退还',
      { type: 'error', confirmButtonText: '确认退还', cancelButtonText: '取消' }
    )
    // 逐个退还
    for (const preset of grantedPresets.value) {
      await api.meRevokePreset(props.capabilityId, preset.id, { reason: '用户主动退还整个能力包' })
    }
    ElMessage.success('退还申请已提交')
    loadData()
    emit('refresh')
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '退还失败')
    }
  }
}

function applyPreset(preset: any) {
  // 跳转到能力市场申请页面
  window.open(`/marketplace?capability=${props.capabilityId}&preset=${preset.id}`, '_blank')
}
</script>

<style scoped>
.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 40px;
  color: var(--text-secondary);
}

.error-state {
  color: var(--danger);
}

.manage-content {
  max-height: 60vh;
  overflow-y: auto;
}

.cap-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--bg-inset);
  border-radius: 12px;
  margin-bottom: 20px;
}

.cap-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: var(--brand-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.cap-name {
  font-size: 16px;
  font-weight: 700;
}

.cap-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.empty-tip {
  padding: 20px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  background: var(--bg-card);
  border-radius: 8px;
  border: 1px dashed var(--border);
}

.preset-card {
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-bottom: 10px;
  transition: all 0.2s;
}

.preset-card:hover {
  box-shadow: var(--shadow-sm);
}

.preset-card.granted {
  background: var(--success-bg);
  border-color: var(--success);
}

.preset-card.available {
  background: var(--bg-card);
}

.preset-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.preset-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
}

.preset-status.granted {
  background: var(--success);
  color: #fff;
}

.preset-status.available {
  background: var(--bg-inset);
  color: var(--text-tertiary);
  border: 1px solid var(--border);
}

.preset-name {
  font-size: 14px;
  font-weight: 600;
}

.preset-interfaces {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.iface-tag {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 2px 6px;
  background: var(--bg-inset);
  border: 1px solid var(--border);
  border-radius: 4px;
}

.preset-grant-info {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-tertiary);
  margin-bottom: 10px;
}

.preset-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.footer-actions {
  display: flex;
  justify-content: space-between;
  padding-top: 16px;
  border-top: 1px solid var(--border);
  margin-top: 16px;
}
</style>
