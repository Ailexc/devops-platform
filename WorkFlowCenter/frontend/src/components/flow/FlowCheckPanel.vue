<template>
  <div class="flow-check-panel">
    <!-- 顶部概览 -->
    <div class="check-overview" :class="overviewClass">
      <div class="overview-status">
        <el-icon :size="40" class="overview-icon">
          <component :is="overviewIcon" />
        </el-icon>
        <div class="overview-text">
          <h3>{{ overviewTitle }}</h3>
          <p>{{ overviewMessage }}</p>
        </div>
      </div>
      <div class="overview-stats">
        <div class="stat-item">
          <span class="stat-value">{{ summary.total }}</span>
          <span class="stat-label">检查项</span>
        </div>
        <div class="stat-item success">
          <span class="stat-value">{{ summary.passed }}</span>
          <span class="stat-label">通过</span>
        </div>
        <div class="stat-item warning">
          <span class="stat-value">{{ summary.warnings }}</span>
          <span class="stat-label">警告</span>
        </div>
        <div class="stat-item danger">
          <span class="stat-value">{{ summary.errors }}</span>
          <span class="stat-label">错误</span>
        </div>
      </div>
    </div>

    <!-- 检查分类 -->
    <div v-loading="loading" class="check-categories">
      <el-collapse v-model="activeNames">
        <el-collapse-item
          v-for="category in categories"
          :key="category.name"
          :name="category.name"
        >
          <template #title>
            <div class="category-title">
              <el-icon class="category-icon">
                <component :is="categoryIcons[category.icon] || Document" />
              </el-icon>
              <span class="category-name">{{ category.name }}</span>
              <el-tag
                :type="category.passed ? 'success' : 'danger'"
                size="small"
                effect="light"
                round
              >
                {{ category.passed ? '通过' : '存在问题' }}
              </el-tag>
            </div>
          </template>

          <div class="check-list">
            <div
              v-for="(check, idx) in category.checks"
              :key="idx"
              class="check-item"
              :class="`check-item--${check.status}`"
            >
              <el-icon class="check-icon">
                <CircleCheckFilled v-if="check.status === 'passed'" />
                <WarningFilled v-else-if="check.status === 'warning'" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span class="check-name">{{ check.name }}</span>
              <span class="check-message">{{ check.message }}</span>
              <el-button
                v-if="check.fixAction"
                type="primary"
                link
                size="small"
                @click="handleFix(check.fixAction)"
              >
                去修复
              </el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <el-empty
        v-if="!loading && categories.length === 0"
        description="暂无检查结果，请点击「开始检查」"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  Document,
  Memo,
  Share,
  Link,
  Connection,
  SetUp
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'fix'])

const activeNames = ref([])
const categoryIcons = {
  document: Document,
  form: Memo,
  share: Share,
  link: Link,
  connection: Connection,
  'set-up': SetUp
}

const result = computed(() => props.modelValue)

const summary = computed(() =>
  result.value?.summary || { total: 0, passed: 0, warnings: 0, errors: 0 }
)

const categories = computed(() => result.value?.categories || [])

const passed = computed(() => result.value?.passed ?? true)

const overviewClass = computed(() => {
  if (!result.value) return 'idle'
  if (summary.value.errors > 0) return 'danger'
  if (summary.value.warnings > 0) return 'warning'
  return 'success'
})

const overviewIcon = computed(() => {
  if (!result.value) return Document
  if (summary.value.errors > 0) return CircleCloseFilled
  if (summary.value.warnings > 0) return WarningFilled
  return CircleCheckFilled
})

const overviewTitle = computed(() => {
  if (!result.value) return '尚未检查'
  if (summary.value.errors > 0) return '检查未通过'
  if (summary.value.warnings > 0) return '检查通过（有警告）'
  return '全部检查通过'
})

const overviewMessage = computed(() => {
  if (!result.value) return '进入本步骤后将自动执行流程检查'
  if (summary.value.errors > 0) {
    return `发现 ${summary.value.errors} 个错误，请修复后再发布`
  }
  if (summary.value.warnings > 0) {
    return `发现 ${summary.value.warnings} 个警告，建议处理后再发布`
  }
  return `共检查 ${summary.value.total} 项，全部通过`
})

// 展开存在问题的分类
watch(
  () => categories.value,
  (cats) => {
    const names = cats
      .filter(c => !c.passed)
      .map(c => c.name)
    activeNames.value = names
  },
  { immediate: true, deep: true }
)

const handleFix = (fixAction) => {
  emit('fix', fixAction)
}
</script>

<style scoped lang="scss">
.flow-check-panel {
  .check-overview {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 20px;
    transition: all 0.3s;

    &.idle {
      background: #f5f7fa;
      border: 1px dashed #dcdfe6;
    }

    &.success {
      background: linear-gradient(135deg, #f0f9eb 0%, #f5faf0 100%);
      border: 1px solid #e1f3d8;
    }

    &.warning {
      background: linear-gradient(135deg, #fdf6ec 0%, #fdfaf5 100%);
      border: 1px solid #faecd8;
    }

    &.danger {
      background: linear-gradient(135deg, #fef0f0 0%, #fdf6f6 100%);
      border: 1px solid #fde2e2;
    }

    .overview-status {
      display: flex;
      align-items: center;
      gap: 16px;

      .overview-icon {
        color: #909399;

        .success & {
          color: #67c23a;
        }

        .warning & {
          color: #e6a23c;
        }

        .danger & {
          color: #f56c6c;
        }
      }

      .overview-text {
        h3 {
          margin: 0 0 4px;
          font-size: 18px;
          color: #303133;
        }

        p {
          margin: 0;
          font-size: 13px;
          color: #909399;
        }
      }
    }

    .overview-stats {
      display: flex;
      gap: 24px;

      .stat-item {
        text-align: center;

        .stat-value {
          display: block;
          font-size: 24px;
          font-weight: 600;
          color: #303133;
        }

        .stat-label {
          font-size: 12px;
          color: #909399;
        }

        &.success .stat-value {
          color: #67c23a;
        }

        &.warning .stat-value {
          color: #e6a23c;
        }

        &.danger .stat-value {
          color: #f56c6c;
        }
      }
    }
  }

  .check-categories {
    min-height: 200px;

    .category-title {
      display: flex;
      align-items: center;
      gap: 8px;

      .category-icon {
        color: #409eff;
        font-size: 16px;
      }

      .category-name {
        font-weight: 500;
        color: #303133;
      }
    }

    .check-list {
      padding: 0 8px;

      .check-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 6px;
        margin-bottom: 4px;

        &:hover {
          background: #f5f7fa;
        }

        &--passed {
          .check-icon {
            color: #67c23a;
          }

          .check-message {
            color: #909399;
          }
        }

        &--warning {
          background: #fdf6ec;

          .check-icon {
            color: #e6a23c;
          }
        }

        &--error {
          background: #fef0f0;

          .check-icon {
            color: #f56c6c;
          }
        }

        .check-icon {
          font-size: 16px;
          flex-shrink: 0;
        }

        .check-name {
          font-size: 13px;
          font-weight: 500;
          color: #303133;
          flex-shrink: 0;
          min-width: 90px;
        }

        .check-message {
          flex: 1;
          font-size: 13px;
          color: #606266;
          word-break: break-all;
        }
      }
    }
  }
}
</style>
