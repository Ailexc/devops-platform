<template>
  <div class="user-selector">
    <el-popover
      v-model:visible="visible"
      trigger="click"
      placement="bottom-start"
      :width="420"
      popper-class="user-selector-popover"
    >
      <template #reference>
        <!-- 只依赖 el-popover 的 trigger="click"，避免手动切换导致弹窗瞬间关闭 -->
        <div class="selector-trigger">
          <template v-if="selectedItems.length > 0">
            <el-tag
              v-for="item in selectedItems"
              :key="item.id"
              closable
              size="small"
              @close="removeItem(item)"
            >
              {{ item.name }}
            </el-tag>
          </template>
          <span v-else class="placeholder">{{ placeholder }}</span>
          <el-icon class="arrow"><ArrowDown /></el-icon>
        </div>
      </template>

      <div class="selector-panel">
        <el-tabs v-model="activeTab">
          <el-tab-pane v-if="modes.includes('user')" label="用户" name="user">
            <el-input
              v-model="userKeyword"
              placeholder="搜索用户..."
              clearable
              size="small"
              class="search-input"
            />
            <div class="option-list">
              <div
                v-for="user in filteredUsers"
                :key="user.id"
                class="option-item"
                :class="{ selected: isSelected(user.id) }"
                @click="toggleUser(user)"
              >
                <el-avatar :size="24" class="option-avatar">
                  {{ user.name?.charAt(0) }}
                </el-avatar>
                <span class="option-name">{{ user.name }}</span>
                <span class="option-sub">{{ user.username }}</span>
                <el-icon v-if="isSelected(user.id)" class="check"><Check /></el-icon>
              </div>
              <div v-if="filteredUsers.length === 0" class="option-empty">
                暂无匹配用户
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="modes.includes('dept')" label="部门" name="dept">
            <div class="option-list">
              <div
                v-for="dept in allDepts"
                :key="dept.id"
                class="option-item"
                :class="{ selected: isSelected(dept.id) }"
                @click="toggleDept(dept)"
              >
                <el-icon class="option-icon"><Folder /></el-icon>
                <span class="option-name">{{ dept.name }}</span>
                <el-icon v-if="isSelected(dept.id)" class="check"><Check /></el-icon>
              </div>
              <div v-if="allDepts.length === 0" class="option-empty">
                暂无部门数据
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane v-if="modes.includes('role')" label="角色" name="role">
            <div class="option-list">
              <div
                v-for="role in allRoles"
                :key="role.id"
                class="option-item"
                :class="{ selected: isSelected(role.id) }"
                @click="toggleRole(role)"
              >
                <el-icon class="option-icon"><User /></el-icon>
                <span class="option-name">{{ role.name }}</span>
                <el-icon v-if="isSelected(role.id)" class="check"><Check /></el-icon>
              </div>
              <div v-if="allRoles.length === 0" class="option-empty">
                暂无角色数据
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>

        <div class="panel-footer">
          <span class="selected-count">已选 {{ selectedItems.length }} 项</span>
          <el-button size="small" type="primary" @click="visible = false">
            完成
          </el-button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ArrowDown, Check, Folder, User } from '@element-plus/icons-vue'
import { useOrganStore } from '@/stores'
import { loadOrgan } from '@/api/modules/organ'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  // 可选模式: user / dept / role
  modes: {
    type: Array,
    default: () => ['user']
  },
  placeholder: {
    type: String,
    default: '请选择'
  },
  multiple: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue'])

const organStore = useOrganStore()
const visible = ref(false)
const activeTab = ref(props.modes[0] || 'user')
const userKeyword = ref('')

const allUsers = computed(() => organStore.allUsers || [])
const allDepts = computed(() => organStore.allDepts || [])
const allRoles = computed(() => organStore.allRoles || [])

const selectedItems = computed(() => {
  const items = []
  props.modelValue.forEach(id => {
    const item = organStore.getById(id)
    if (item && item.name !== '未知') {
      items.push(item)
    }
  })
  return items
})

const filteredUsers = computed(() => {
  const kw = userKeyword.value.toLowerCase()
  if (!kw) return allUsers.value
  return allUsers.value.filter(u =>
    (u.name || '').toLowerCase().includes(kw) ||
    (u.username || '').toLowerCase().includes(kw)
  )
})

const isSelected = (id) => props.modelValue.includes(id)

const emitChange = (newIds) => {
  emit('update:modelValue', newIds)
}

const toggleUser = (user) => {
  let ids = [...props.modelValue]
  if (props.multiple) {
    if (ids.includes(user.id)) {
      ids = ids.filter(i => i !== user.id)
    } else {
      ids.push(user.id)
    }
  } else {
    ids = [user.id]
    visible.value = false
  }
  emitChange(ids)
}

const toggleDept = (dept) => {
  let ids = [...props.modelValue]
  if (ids.includes(dept.id)) {
    ids = ids.filter(i => i !== dept.id)
  } else {
    ids.push(dept.id)
  }
  emitChange(ids)
}

const toggleRole = (role) => {
  let ids = [...props.modelValue]
  if (ids.includes(role.id)) {
    ids = ids.filter(i => i !== role.id)
  } else {
    ids.push(role.id)
  }
  emitChange(ids)
}

const removeItem = (item) => {
  emitChange(props.modelValue.filter(i => i !== item.id))
}

watch(
  () => props.modelValue,
  () => {},
  { deep: true }
)

onMounted(() => {
  loadOrgan()
})
</script>

<style scoped lang="scss">
.user-selector {
  width: 100%;

  .selector-trigger {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    min-height: 32px;
    padding: 3px 10px;
    border: 1px solid #dcdfe6;
    border-radius: 6px;
    cursor: pointer;
    background: #fff;
    transition: border-color 0.2s;

    &:hover {
      border-color: #409eff;
    }

    .placeholder {
      color: #c0c4cc;
      font-size: 13px;
      flex: 1;
    }

    .arrow {
      color: #c0c4cc;
      margin-left: auto;
    }
  }
}

.selector-panel {
  .search-input {
    margin-bottom: 10px;
  }

  .option-list {
    max-height: 280px;
    overflow-y: auto;
  }

  .option-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;

    &:hover {
      background: #f5f7fa;
    }

    &.selected {
      background: #ecf5ff;
    }

    .option-avatar {
      background: #409eff;
      color: #fff;
      font-size: 12px;
      flex-shrink: 0;
    }

    .option-icon {
      color: #909399;
      font-size: 18px;
    }

    .option-name {
      flex: 0 0 auto;
      font-size: 13px;
      color: #303133;
    }

    .option-sub {
      flex: 1;
      font-size: 12px;
      color: #909399;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .check {
      color: #409eff;
    }
  }

  .option-empty {
    text-align: center;
    color: #909399;
    padding: 20px 0;
    font-size: 13px;
  }

  .panel-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #ebeef5;

    .selected-count {
      font-size: 12px;
      color: #909399;
    }
  }
}
</style>
