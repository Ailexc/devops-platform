<template>
  <div class="im-channel-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="page-header-icon"><el-icon><ChatDotRound /></el-icon></div>
      <div>
        <h1>协同渠道</h1>
        <p class="page-header-desc">IM 卡片办理 · 通知推送</p>
      </div>
    </div>

    <!-- 真实业务场景 -->
    <el-card class="scene-card" shadow="never">
      <template #header><span>真实业务场景</span></template>
      <p class="scene-desc">
        用户无需进入工单系统，直接在<strong>办公通讯软件（当前为飞书）</strong>中接收通知并办理审批——
        协同渠道让待办"主动找人"：
      </p>
      <div class="channel-grid">
        <div class="channel-block">
          <div class="channel-block__head">
            <el-tag type="primary" effect="dark" size="small">入站</el-tag>
            <span class="channel-block__name">IM 卡片办理</span>
          </div>
          <p class="channel-block__desc">飞书卡片展示待办表单与办理动作，用户<strong>在卡片内直接审批 / 填单</strong>，结果回调工单系统。</p>
        </div>
        <div class="channel-block">
          <div class="channel-block__head">
            <el-tag type="warning" effect="dark" size="small">出站</el-tag>
            <span class="channel-block__name">IM 通知推送</span>
          </div>
          <p class="channel-block__desc">审批提醒、结果通知通过<strong>消息中心统一出口</strong>推送到 IM，工单系统不直连通讯软件。</p>
        </div>
      </div>
      <p class="scene-hint">
        关键原则：<strong>对外发消息一律走消息中心</strong>（统一出口、多渠道扩展、限流熔断、审计），
        不直接调用通讯软件接口；未来扩展企业微信 / 钉钉只需在消息中心增加渠道。
      </p>
    </el-card>

    <!-- 渠道配置（规划） -->
    <el-card class="config-card" shadow="never">
      <template #header><span>IM 渠道配置</span></template>
      <el-table :data="channels" border stripe>
        <el-table-column prop="name" label="渠道" min-width="120" />
        <el-table-column prop="type" label="用途" min-width="140" />
        <el-table-column label="接入方式" min-width="200">
          <template #default="{ row }">
            <code class="code-badge">{{ row.mode }}</code>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === '已接入' ? 'success' : 'info'" size="small">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="note" label="说明" min-width="220" show-overflow-tooltip />
      </el-table>
      <div class="config-hint">
        Demo 说明：真实业务中本系统与飞书交互（卡片办理 + 消息推送）；当前演示环境为方便展示，
        以<strong>站内待办 + 通知中心</strong>模拟该机制，卡片办理与 IM 推送作为后续落地方向。
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ChatDotRound } from '@element-plus/icons-vue'

const channels = ref([
  {
    name: '飞书',
    type: '卡片办理 + 通知',
    mode: '飞书应用接入（AppID / AppSecret）',
    status: '已接入',
    note: '真实业务：飞书卡片查看/办理待办，通知经消息中心推送'
  },
  {
    name: '企业微信',
    type: '通知推送',
    mode: '消息中心渠道扩展',
    status: '规划',
    note: '通过消息中心扩展，无需改动工单系统'
  },
  {
    name: '钉钉',
    type: '通知推送',
    mode: '消息中心渠道扩展',
    status: '规划',
    note: '通过消息中心扩展，无需改动工单系统'
  }
])
</script>

<style scoped lang="scss">
.im-channel-list {
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
      font-size: 13px;
      color: #4e5969;
      line-height: 1.7;

      strong {
        color: #165dff;
      }
    }
  }

  .scene-hint {
    margin: 0;
    font-size: 12.5px;
    color: #86909c;
    line-height: 1.8;
    border-top: 1px dashed #e5e9f2;
    padding-top: 12px;

    strong {
      color: #165dff;
    }
  }
}

.config-card {
  .code-badge {
    background: #f2f3f5;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
    color: #4e5969;
  }

  .config-hint {
    margin-top: 14px;
    font-size: 12.5px;
    color: #86909c;
    line-height: 1.8;
    border-top: 1px dashed #e5e9f2;
    padding-top: 12px;

    strong {
      color: #165dff;
    }
  }
}
</style>
