<template>
  <div class="channel-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><Connection /></el-icon></div>
        <div>
          <h1>消息通道</h1>
          <p class="page-header-desc">对外订阅 · 主动推送</p>
        </div>
      </div>
    </div>

    <!-- 真实业务场景 -->
    <el-card class="scene-card" shadow="never">
      <template #header><span>真实业务场景</span></template>
      <p class="scene-desc">
        异步消息统一走消息通道：外部任务的执行状态<strong>实时回流</strong>，本系统也<strong>主动推送</strong>事件给外部平台。
        （同步 HTTP API 走「开放 API」页，本页只承载<strong>异步消息</strong>）
      </p>
      <div class="channel-grid">
        <div class="channel-block">
          <div class="channel-block__head">
            <el-tag type="primary" effect="dark" size="small">通道 ①</el-tag>
            <span class="channel-block__name">对外订阅（接收）</span>
          </div>
          <p class="channel-block__desc">队列订阅 <code>workflow.task.status</code>，<strong>实时获取执行进度（含中间态）</strong>，区别于回调只能拿最终态。</p>
        </div>
        <div class="channel-block">
          <div class="channel-block__head">
            <el-tag type="warning" effect="dark" size="small">通道 ②</el-tag>
            <span class="channel-block__name">主动推送（上报）</span>
          </div>
          <p class="channel-block__desc">工单事件<strong>推送到审计 / 变更中心</strong>（工单全量、变更单），实现全链路审计与变更管控。</p>
        </div>
      </div>
      <p class="scene-hint">Demo 中模拟这一机制：外部能力（CMDB / DNS / 邮件 / 权限中心等）执行结果经队列订阅回流，工单事件经主动推送上报。</p>
    </el-card>

    <!-- 对外订阅通道 -->
    <el-card class="mq-card" shadow="never">
      <template #header><span>对外订阅通道（对外暴露）</span></template>
      <div class="mq">
        <span class="mq__label">主题 / 队列</span>
        <code class="mq__name">workflow.task.status</code>
        <el-tag size="small" type="warning" effect="plain">外部任务平台投递</el-tag>
      </div>
      <div class="mq-events">
        <span class="mq-events__label">订阅事件</span>
        <el-tag v-for="e in mqEvents" :key="e" size="small" effect="plain" class="mq-events__tag">{{ e }}</el-tag>
      </div>
      <p class="mq-desc">
        本系统<strong>对外暴露的订阅通道</strong>：外部任务平台向 <code>workflow.task.status</code> 主题投递状态消息
        （排队 / 执行中 / 成功 / 失败），本系统实时消费并更新节点状态——含中间态，区别于回调只能拿最终态。
      </p>
    </el-card>

    <!-- 订阅通道（接收订阅 + 推送上报） -->
    <el-card class="sub-card" shadow="never" v-loading="loading">
      <template #header><span>订阅通道</span></template>
      <p class="sub-desc">
        以下均为<strong>订阅通道</strong>，区别只在<strong>行为</strong>：<el-tag size="small" type="primary" effect="plain">接收订阅</el-tag> 为本系统订阅外部消息；
        <el-tag size="small" type="warning" effect="plain">推送上报</el-tag> 为外部平台订阅本系统消息。
      </p>
      <el-table :data="subscriptions" border stripe>
        <el-table-column prop="name" label="通道名称" min-width="170" />
        <el-table-column label="主题 / 目标通道" min-width="220">
          <template #default="{ row }">
            <code class="code-badge">{{ row.channel }}</code>
          </template>
        </el-table-column>
        <el-table-column label="行为" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.behavior === 'receive' ? 'primary' : 'warning'" size="small">
              {{ row.behavior === 'receive' ? '接收订阅' : '推送上报' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="订阅事件" min-width="220">
          <template #default="{ row }">
            <el-tooltip v-for="evt in row.events" :key="evt" :content="evt" placement="top">
              <el-tag size="small" effect="plain" class="event-tag">{{ eventLabel(evt) }}</el-tag>
            </el-tooltip>
            <span v-if="!row.events?.length">-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '启用' : '停用' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loading && !subscriptions.length" class="sub-empty">暂无订阅通道</div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Connection } from '@element-plus/icons-vue'
import { getWebhooks } from '@/api/modules/events'
import { eventLabel } from '@/utils/event-labels'

const loading = ref(false)
const subs = ref([])
const subscriptions = ref([])
const mqEvents = ['process.started', 'task.completed', 'task.failed', 'process.completed']

// 订阅通道：接收订阅（direction=receive）+ 推送上报（direction=push），由后端方向字段决定行为
const buildSubscriptions = () => {
  subscriptions.value = (subs.value || []).map((s) => ({
    name: s.name,
    channel: s.url,
    behavior: s.direction === 'push' ? 'push' : 'receive',
    events: s.events || [],
    is_active: s.is_active
  }))
}

const fetchSubs = async () => {
  loading.value = true
  try {
    const response = await getWebhooks({ page: 1, page_size: 100 })
    const data = response?.data ?? response
    subs.value = Array.isArray(data) ? data : (data?.results || [])
  } catch (e) {
    console.error('获取订阅通道失败:', e)
  } finally {
    buildSubscriptions()
    loading.value = false
  }
}

onMounted(fetchSubs)
</script>

<style scoped lang="scss">
.channel-list {
  padding: 24px;
  background: #f7f8fa;
  min-height: 100%;
  max-width: 1080px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
  display: flex;
  align-items: flex-start;
  gap: 12px;

  .page-header-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    background: #ecf5ff;
    color: #409eff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }

  h1 {
    margin: 0 0 4px;
    font-size: 22px;
    color: #1d2129;
  }

  .page-header-desc {
    margin: 0;
    font-size: 13px;
    color: #86909c;
  }
}

.el-card {
  border-radius: 12px;
  margin-bottom: 16px;
}

.outbound-card {
  .outbound-desc {
    margin: 0 0 14px;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.8;

    strong {
      color: #165dff;
    }
  }
}

.sub-card {
  .sub-desc {
    margin: 0 0 14px;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.8;

    strong {
      color: #165dff;
    }
  }

  .code-badge {
    background: #f2f3f5;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: #4e5969;
  }
}

.scene-card {
  .scene-desc {
    margin: 0 0 14px;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.8;

    strong {
      color: #165dff;
    }
  }

  .channel-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 14px;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .channel-block {
    background: #f7faff;
    border: 1px solid #e5e9f2;
    border-radius: 10px;
    padding: 14px 16px;

    .channel-block__head {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      .channel-block__name {
        font-size: 14px;
        font-weight: 600;
        color: #1d2129;
      }
    }

    .channel-block__desc {
      margin: 0;
      font-size: 12px;
      color: #4e5969;
      line-height: 1.7;

      strong {
        color: #165dff;
      }
    }
  }

  .scene-hint {
    margin: 0;
    font-size: 12px;
    color: #86909c;
  }
}

.endpoint-card,
.mq-card {
  .endpoint,
  .mq {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 10px;

    .endpoint__method {
      background: #409eff;
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      padding: 3px 10px;
      border-radius: 4px;
    }

    .endpoint__url,
    .mq__name {
      font-family: ui-monospace, monospace;
      font-size: 14px;
      color: #1d2129;
      background: #f2f3f5;
      border-radius: 6px;
      padding: 4px 10px;
    }

    .mq__label {
      font-size: 13px;
      color: #86909c;
    }
  }

  .endpoint-desc,
  .mq-desc {
    margin: 0;
    font-size: 13px;
    color: #4e5969;
    line-height: 1.8;

    code {
      font-family: ui-monospace, monospace;
      color: #165dff;
      background: #eef4ff;
      border-radius: 4px;
      padding: 1px 5px;
    }
  }

  .mq-events {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 10px;

    .mq-events__label {
      font-size: 13px;
      color: #86909c;
    }
  }
}

.sub-card {
  .event-tag {
    margin-right: 4px;
    margin-bottom: 2px;
  }

  .sub-empty {
    text-align: center;
    color: #c9cdd4;
    padding: 24px 0;
    font-size: 13px;
  }
}
</style>
