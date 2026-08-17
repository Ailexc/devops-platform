<template>
  <el-popover
    v-model:visible="visible"
    trigger="click"
    placement="bottom-start"
    :width="360"
    popper-class="icon-picker-popover"
  >
    <template #reference>
      <div class="icon-picker-trigger" @click="visible = !visible">
        <el-icon class="icon-preview" :size="20">
          <component :is="currentIcon" />
        </el-icon>
        <span class="icon-name">{{ modelValue || '选择图标' }}</span>
        <el-icon class="arrow"><ArrowDown /></el-icon>
      </div>
    </template>

    <div class="icon-picker-panel">
      <el-input
        v-model="keyword"
        placeholder="搜索图标..."
        clearable
        size="small"
        class="icon-search"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <div class="icon-grid">
        <div
          v-for="icon in filteredIcons"
          :key="icon"
          class="icon-item"
          :class="{ active: modelValue === icon }"
          :title="icon"
          @click="selectIcon(icon)"
        >
          <el-icon :size="18"><component :is="iconComponents[icon]" /></el-icon>
        </div>
      </div>
      <div v-if="filteredIcons.length === 0" class="icon-empty">
        未找到匹配的图标
      </div>
    </div>
  </el-popover>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowDown, Search } from '@element-plus/icons-vue'
import * as Icons from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'document'
  }
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const keyword = ref('')

// 推荐图标列表（流程场景常用）
const iconNames = [
  'Document', 'DocumentAdd', 'DocumentChecked', 'DocumentCopy', 'DocumentDelete',
  'EditPen', 'Edit', 'Notebook', 'Tickets', 'Memo',
  'Calendar', 'Clock', 'Timer', 'AlarmClock',
  'User', 'UserFilled', 'Avatar', 'UserFilled',
  'Folder', 'FolderOpened', 'Files', 'FolderChecked',
  'Money', 'Wallet', 'CreditCard', 'Coin', 'Sell',
  'ShoppingCart', 'ShoppingBag', 'Goods', 'Box',
  'House', 'OfficeBuilding', 'School', 'Location',
  'Setting', 'Tools', 'Operation', 'SwitchButton',
  'ChatDotRound', 'Message', 'Bell', 'Phone',
  'Star', 'StarFilled', 'Flag', 'Medal',
  'DataAnalysis', 'TrendCharts', 'PieChart', 'Histogram',
  'Connection', 'Link', 'Share', 'Promotion',
  'Checked', 'CircleCheck', 'CircleCheckFilled',
  'Warning', 'WarningFilled', 'InfoFilled',
  'Plus', 'Minus', 'Search', 'Upload', 'Download', 'Refresh', 'Lock', 'Unlock'
]

const iconComponents = {}
iconNames.forEach(name => {
  if (Icons[name]) {
    iconComponents[name] = Icons[name]
  }
})

const availableNames = Object.keys(iconComponents)

const filteredIcons = computed(() => {
  const kw = keyword.value.toLowerCase()
  if (!kw) return availableNames
  return availableNames.filter(name => name.toLowerCase().includes(kw))
})

const currentIcon = computed(() => {
  return iconComponents[props.modelValue] || Icons.Document
})

const selectIcon = (icon) => {
  emit('update:modelValue', icon)
  visible.value = false
  keyword.value = ''
}
</script>

<style scoped lang="scss">
.icon-picker-trigger {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 5px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  cursor: pointer;
  background: #fff;
  transition: border-color 0.2s;

  &:hover {
    border-color: #409eff;
  }

  .icon-preview {
    color: #409eff;
  }

  .icon-name {
    flex: 1;
    font-size: 13px;
    color: #606266;
  }

  .arrow {
    color: #c0c4cc;
  }
}

.icon-picker-panel {
  .icon-search {
    margin-bottom: 12px;
  }

  .icon-grid {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 4px;
    max-height: 260px;
    overflow-y: auto;
  }

  .icon-item {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 36px;
    border-radius: 6px;
    cursor: pointer;
    color: #606266;
    transition: all 0.2s;

    &:hover {
      background: #ecf5ff;
      color: #409eff;
    }

    &.active {
      background: #409eff;
      color: #fff;
    }
  }

  .icon-empty {
    text-align: center;
    color: #909399;
    padding: 20px 0;
    font-size: 13px;
  }
}
</style>
