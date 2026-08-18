<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { catalogApi, ticketApi } from '@/api'

const loading = ref(false)
const categories = ref<any[]>([])
const quotaVisible = ref(false)
const quotas = ref<any[]>([])
const applyModalVisible = ref(false)
const selectedItem = ref<any>(null)

const applyForm = reactive({
  spec: '',
  region: 'cn-hangzhou',
  name: '',
})

const allItems = ref<any[]>([])

async function loadCatalog() {
  loading.value = true
  try {
    const { data } = await catalogApi.categories()
    categories.value = data.results
    // 展平所有服务项
    for (const cat of data.results) {
      for (const item of cat.items || []) {
        allItems.value.push({ ...item, category_name: cat.name, category_icon: cat.icon })
      }
    }
  } catch { /* 静默 */ } finally { loading.value = false }
}

async function showQuota() {
  quotaVisible.value = true
  try {
    const { data } = await catalogApi.myQuota()
    quotas.value = data
  } catch { /* 静默 */ }
}

function handleApply(item: any) {
  selectedItem.value = item
  applyForm.spec = item.spec_options?.[0]?.value || ''
  applyForm.region = item.region_options?.[0] || 'cn-hangzhou'
  applyForm.name = ''
  applyModalVisible.value = true
}

async function submitApply() {
  if (!applyForm.name) { message.warning('请输入名称'); return }
  try {
    await ticketApi.create({
      ticket_type: 'create_instance',
      title: `申请${selectedItem.value.name} - ${applyForm.name}`,
      provider_type: 'mock',
      resource_name: applyForm.name,
      request_content: {
        name: applyForm.name,
        region: applyForm.region,
        spec: applyForm.spec,
        account_id: 1,
      },
    })
    message.success('✅ 工单已提交，等待审批')
    applyModalVisible.value = false
  } catch { message.error('提交失败') }
}

onMounted(loadCatalog)
</script>

<template>
  <div>
    <a-page-header title="🏪 服务中心" sub-title="自助申请云资源，自动交付">
      <template #extra>
        <a-button @click="showQuota">📊 我的配额</a-button>
      </template>
    </a-page-header>

    <a-spin :spinning="loading">
      <!-- 服务卡片网格 -->
      <a-row :gutter="[16, 16]">
        <a-col :span="8" v-for="item in allItems" :key="item.id">
          <a-card hoverable style="height: 100%">
            <template #title>
              <div style="display: flex; align-items: center; gap: 8px">
                <span style="font-size: 24px">{{ item.icon || '📦' }}</span>
                <div>
                  <div style="font-weight: 600">{{ item.name }}</div>
                  <div style="font-size: 12px; color: #999">{{ item.category_icon }} {{ item.category_name }}</div>
                </div>
              </div>
            </template>
            <p style="color: #666; margin-bottom: 12px">{{ item.description || '企业级云服务，选规格即可一键申请' }}</p>
            <!-- 规格选项 -->
            <div v-if="item.spec_options?.length" style="margin-bottom: 12px">
              <div style="font-size: 12px; color: #999; margin-bottom: 4px">可选规格：</div>
              <a-space direction="vertical" :size="4" style="width: 100%">
                <div v-for="spec in item.spec_options" :key="spec.value"
                     style="display: flex; justify-content: space-between; padding: 4px 8px; background: #fafafa; border-radius: 4px; font-size: 12px">
                  <span>{{ spec.label }}</span>
                  <span style="color: #ff4d4f; font-weight: 500">¥{{ spec.price }}/月</span>
                </div>
              </a-space>
            </div>
            <!-- 地域 -->
            <div v-if="item.region_options?.length" style="margin-bottom: 12px">
              <div style="font-size: 12px; color: #999; margin-bottom: 4px">支持地域：</div>
              <a-space wrap>
                <a-tag v-for="r in item.region_options" :key="r" size="small">{{ r }}</a-tag>
              </a-space>
            </div>
            <template #actions>
              <a-button type="primary" size="small" @click="handleApply(item)">立即申请</a-button>
            </template>
          </a-card>
        </a-col>
      </a-row>
    </a-spin>

    <!-- 申请弹窗 -->
    <a-modal v-model:open="applyModalVisible" :title="`申请 ${selectedItem?.name || ''}`" @ok="submitApply" :width="500">
      <a-form layout="vertical">
        <a-form-item label="资源名称" required>
          <a-input v-model:value="applyForm.name" placeholder="请输入名称，如 web-prod-01" />
        </a-form-item>
        <a-form-item label="规格" required>
          <a-select v-model:value="applyForm.spec">
            <a-select-option v-for="spec in selectedItem?.spec_options || []" :key="spec.value" :value="spec.value">
              {{ spec.label }} - ¥{{ spec.price }}/月
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="地域" required>
          <a-select v-model:value="applyForm.region">
            <a-select-option v-for="r in selectedItem?.region_options || []" :key="r" :value="r">{{ r }}</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
      <template #footer>
        <a-button @click="applyModalVisible = false">取消</a-button>
        <a-button type="primary" @click="submitApply">提交工单</a-button>
      </template>
    </a-modal>

    <!-- 配额抽屉 -->
    <a-drawer v-model:open="quotaVisible" title="📊 我的部门配额" :width="420">
      <a-alert message="配额按部门分配，由管理员统一管理" type="info" show-icon style="margin-bottom: 16px" />
      <a-table
        :columns="[
          { title: '服务', dataIndex: 'service_item_name' },
          { title: '已用', dataIndex: 'used', width: 80 },
          { title: '上限', dataIndex: 'quota_limit', width: 80 },
          { title: '剩余', dataIndex: 'available', width: 80 },
          { title: '使用率', key: 'usage', width: 120 },
        ]"
        :data-source="quotas"
        row-key="id"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'usage'">
            <a-progress :percent="Math.round(record.used / record.quota_limit * 100)" size="small"
                        :status="record.available <= 0 ? 'exception' : 'active'" />
          </template>
        </template>
      </a-table>
    </a-drawer>
  </div>
</template>
