<template>
  <div class="rule-panel">
    <div class="rp-head">
      <span class="rp-desc">
        配置提单预检的业务规则：<b>下拉选数据源 → 选操作符 → 填/引用参考值</b>，底层自动生成 JSON Logic（无需手写表达式）。
        数据源 = 表单字段 + 业务上下文指标（配额 / 容量 / 网络 / 预算 / 历史）。
      </span>
      <el-button type="primary" size="small" @click="openNew">＋ 新增规则</el-button>
    </div>

    <el-empty v-if="!rules.length" description="还没有业务规则，点击「＋ 新增规则」配置第一条" :image-size="70" />

    <div v-for="(r, idx) in rules" :key="r.id || idx" class="rule" :class="'rule--' + r.level">
      <div class="rule-head">
        <span class="rid">{{ r.id || 'RULE-' + String(idx + 1).padStart(3, '0') }}</span>
        <span class="rname">{{ r.name }}</span>
        <el-tag size="small" :type="r.level === 'error' ? 'danger' : 'warning'" effect="light">
          {{ r.level === 'error' ? '错误 · 提交拦截' : '警告 · 提醒附注' }}
        </el-tag>
        <span class="r-actions">
          <el-button size="small" text type="primary" @click="openEdit(r)">编辑</el-button>
          <el-button size="small" text type="danger" @click="remove(r)">删除</el-button>
        </span>
      </div>
      <div class="rule-cond" v-html="human(r)"></div>
      <div class="rule-msg">
        <b>命中提示：</b>{{ r.message || '—' }}
        <b style="margin-left:8px">建议：</b>{{ r.suggestion || '—' }}
      </div>
      <div class="rule-foot">
        <el-tag size="small" effect="plain" style="cursor:pointer" @click="r._open = !r._open">
          {{ r._open ? '收起 JSON Logic' : '查看 JSON Logic' }}
        </el-tag>
      </div>
      <pre v-if="r._open" class="logic-code">{{ buildLogic(r) }}</pre>
    </div>

    <RuleDrawer
      v-model="drawerVisible"
      :rule="editingRule"
      :sources="sources"
      @save="onSave"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RuleDrawer from './drawer/RuleDrawer.vue'
import { groupsHuman, buildLogic, buildSourceGroups } from './common/RuleMeta'

const props = defineProps({
  rules: { type: Array, default: () => [] },
  sources: { type: Object, default: () => ({ form: [], context: [] }) },
})
const emit = defineEmits(['update:rules'])

const sourceGroups = ref(buildSourceGroups(props.sources))

const drawerVisible = ref(false)
const editingRule = ref(null)

let uid = 0
function nextId() {
  uid += 1
  return 'RULE-' + String(uid).padStart(3, '0')
}

const human = (r) => '当 ' + groupsHuman(sourceGroups.value, r.groups || []) + ' 时'

function openNew() {
  editingRule.value = null
  drawerVisible.value = true
}
function openEdit(r) {
  editingRule.value = r
  drawerVisible.value = true
}
function remove(r) {
  const list = [...props.rules]
  const i = list.indexOf(r)
  if (i >= 0) list.splice(i, 1)
  emit('update:rules', list)
}
function onSave(data) {
  const list = [...props.rules]
  if (editingRule.value) {
    const i = list.indexOf(editingRule.value)
    if (i >= 0) list[i] = { ...list[i], ...data }
  } else {
    list.push({ id: nextId(), ...data, _open: false })
  }
  emit('update:rules', list)
}
</script>

<style scoped>
.rule-panel { padding: 4px 0; }
.rp-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.rp-desc { font-size: 13px; color: #4e5969; line-height: 1.7; }
.rule { border: 1px solid #e5e6eb; border-left: 3px solid #c9cdd4; border-radius: 6px; padding: 12px 14px; margin-bottom: 12px; background: #fbfbfc; }
.rule--error { border-left-color: #f53f3f; }
.rule--warning { border-left-color: #ff7d00; }
.rule-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.rid { font-family: ui-monospace, Menlo, monospace; font-size: 12px; color: #165dff; background: #e8f3ff; border-radius: 4px; padding: 1px 6px; font-weight: 600; }
.rname { font-weight: 600; font-size: 13px; }
.r-actions { margin-left: auto; display: flex; gap: 4px; }
.rule-cond { margin-top: 8px; font-size: 13px; color: #4e5969; line-height: 1.7; }
.rule-msg { margin-top: 6px; font-size: 12px; color: #86909c; }
.rule-msg b { color: #1d2129; font-weight: 600; }
.rule-foot { margin-top: 8px; }
.logic-code { font-size: 11px; color: #4e5969; background: #f2f3f5; border-radius: 4px; padding: 8px; white-space: pre-wrap; word-break: break-all; margin-top: 8px; line-height: 1.5; }
:deep(.and) { color: #165dff; }
:deep(.or) { color: #ff7d00; }
</style>
