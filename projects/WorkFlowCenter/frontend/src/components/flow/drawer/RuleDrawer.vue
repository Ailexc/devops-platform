<template>
  <el-drawer
    :model-value="modelValue"
    :title="editing ? '编辑规则' : '新增规则'"
    size="540px"
    @update:model-value="onVisibleChange"
    @open="initDraft"
  >
    <div style="display:flex;flex-direction:column;gap:14px">
      <div>
        <div class="rd-label">规则名称</div>
        <el-input v-model="draft.name" placeholder="如：部门配额检测" />
      </div>

      <div>
        <div class="rd-label">触发条件（多个条件 = 且，多个条件组 = 或）</div>
        <div style="display:flex;flex-direction:column;gap:10px">
          <div v-for="(g, gi) in draft.groups" :key="gi" class="rd-group">
            <div class="rd-group-head">
              <span>条件组 {{ gi + 1 }}</span>
              <el-button size="small" text type="danger" @click="rmGroup(gi)" :disabled="draft.groups.length <= 1">删除组</el-button>
            </div>
            <div v-for="(c, ci) in g" :key="ci" class="rd-cond">
              <div style="display:flex;gap:6px;align-items:center">
                <span class="rd-when">{{ ci === 0 ? '当' : '且' }}</span>
                <el-select v-model="c.source" size="small" placeholder="数据源" style="flex:1.2" @change="onSourceChange(c)">
                  <el-option-group v-for="g2 in sourceGroups" :key="g2.name" :label="g2.name">
                    <el-option v-for="s in g2.items" :key="s.name" :label="s.label" :value="s.name" />
                  </el-option-group>
                </el-select>
                <el-select v-model="c.op" size="small" placeholder="操作符" style="width:110px">
                  <el-option v-for="o in opsFor(c.source)" :key="o" :label="opLabel(o)" :value="o" />
                </el-select>
                <el-button size="small" text type="danger" @click="rmCondition(g, c)" :disabled="g.length <= 1">✕</el-button>
              </div>
              <div style="display:flex;gap:6px;align-items:center;padding-left:40px">
                <span class="rd-when">参考</span>
                <el-radio-group v-model="c.refType" size="small">
                  <el-radio-button value="fixed">固定值</el-radio-button>
                  <el-radio-button value="field">引用字段/指标</el-radio-button>
                </el-radio-group>
                <template v-if="c.refType === 'fixed'">
                  <el-input-number v-if="isNumType(c.source)" v-model="c.fixed" size="small" style="width:130px" :controls="false" />
                  <el-select v-if="isEnumType(c.source)" v-model="c.fixed" size="small" style="width:150px">
                    <el-option v-for="o in (sourceOf(c.source) || {}).options || []" :key="o" :label="o" :value="o" />
                  </el-select>
                  <el-input v-if="isTextType(c.source)" v-model="c.fixed" size="small" placeholder="值" style="width:150px" />
                </template>
                <template v-if="c.refType === 'field'">
                  <el-select v-model="c.refField" size="small" placeholder="选择字段/指标" style="flex:1">
                    <el-option-group v-for="g2 in sourceGroups" :key="g2.name" :label="g2.name">
                      <el-option v-for="s in g2.items" :key="s.name" :label="s.label" :value="s.name" />
                    </el-option-group>
                  </el-select>
                  <el-input-number v-model="c.offset" size="small" placeholder="±" style="width:80px" :controls="false" />
                  <span class="rd-offset">偏移</span>
                </template>
              </div>
            </div>
            <el-button size="small" text type="primary" style="margin-top:6px" @click="addCondition(g)">＋ 添加条件（且）</el-button>
          </div>
        </div>
        <el-button size="small" text type="primary" style="margin-top:6px" @click="addGroup">＋ 添加条件组（或）</el-button>
      </div>

      <div>
        <div class="rd-label">规则行为</div>
        <div style="margin-bottom:8px">
          <el-radio-group v-model="draft.level">
            <el-radio-button value="error">错误 · 提交拦截</el-radio-button>
            <el-radio-button value="warning">警告 · 提醒附注</el-radio-button>
          </el-radio-group>
        </div>
        <el-input v-model="draft.message" size="small" placeholder="命中提示文案（给提单人看）" style="margin-bottom:6px" />
        <el-input v-model="draft.suggestion" size="small" placeholder="建议文案（指导提单人如何修改）" />
      </div>

      <div class="rd-preview">
        <div class="rd-preview-title">实时预览</div>
        <div class="rd-preview-human" v-html="draftHuman"></div>
        <pre class="rd-preview-logic">{{ draftLogic }}</pre>
      </div>
    </div>
    <template #footer>
      <el-button @click="onVisibleChange(false)">取消</el-button>
      <el-button type="primary" @click="save">保存规则</el-button>
    </template>
  </el-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  buildSourceGroups, findSource, opsForType, opLabel,
  groupsHuman, buildLogic, isNumType, isEnumType, isTextType,
} from '../common/RuleMeta'

const props = defineProps({
  modelValue: Boolean,
  rule: { type: Object, default: null }, // null=新增
  sources: { type: Object, default: () => ({ form: [], context: [] }), required: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const sourceGroups = computed(() => buildSourceGroups(props.sources))
const editing = computed(() => !!props.rule)

const draft = ref(null)

function newCond(presetSource) {
  const c = { source: presetSource || '', op: '', refType: 'fixed', fixed: null, refField: '', offset: 0 }
  if (presetSource) c.op = opsForType((findSource(sourceGroups.value, presetSource) || {}).type)[0]
  return c
}

function initDraft() {
  if (props.rule) {
    draft.value = JSON.parse(JSON.stringify({
      name: props.rule.name,
      level: props.rule.level,
      message: props.rule.message,
      suggestion: props.rule.suggestion,
      groups: props.rule.groups || [[newCond()]],
    }))
  } else {
    draft.value = { name: '', level: 'error', message: '', suggestion: '', groups: [[newCond()]] }
  }
}

function onVisibleChange(v) {
  emit('update:modelValue', v)
}

const sourceOf = (name) => findSource(sourceGroups.value, name) || {}
const opsFor = (name) => opsForType((sourceOf(name) || {}).type || 'text')
const isNum = (n) => isNumType(sourceGroups.value, n)
const isEnum = (n) => isEnumType(sourceGroups.value, n)
const isText = (n) => isTextType(sourceGroups.value, n)

function onSourceChange(c) {
  c.op = opsFor(c.source)[0]
  c.fixed = null
  c.refField = ''
}
function addCondition(g) { g.push(newCond()) }
function rmCondition(g, c) { if (g.length > 1) g.splice(g.indexOf(c), 1) }
function addGroup() { draft.value.groups.push([newCond()]) }
function rmGroup(gi) { if (draft.value.groups.length > 1) draft.value.groups.splice(gi, 1) }

const draftHuman = computed(() => (draft.value ? '当 ' + groupsHuman(sourceGroups.value, draft.value.groups) + ' 时 → 命中提示' : ''))
const draftLogic = computed(() => (draft.value ? buildLogic(draft.value) : ''))

function save() {
  const d = draft.value
  if (!d.name) { ElMessage.warning('请填写规则名称'); return }
  for (const g of d.groups) {
    for (const c of g) {
      if (!c.source) { ElMessage.warning('请选择数据源'); return }
      if (!c.op) { ElMessage.warning('请选择操作符'); return }
      if (c.refType === 'fixed' && (c.fixed === null || c.fixed === '')) { ElMessage.warning('请填写参考值'); return }
      if (c.refType === 'field' && !c.refField) { ElMessage.warning('请选择引用的字段/指标'); return }
    }
  }
  emit('save', {
    name: d.name,
    level: d.level,
    message: d.message,
    suggestion: d.suggestion,
    groups: d.groups,
  })
  onVisibleChange(false)
}
</script>

<style scoped>
.rd-label { font-size: 13px; color: #4e5969; margin-bottom: 6px; font-weight: 600; }
.rd-group { border: 1px solid #e5e6eb; border-radius: 8px; padding: 10px; }
.rd-group-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 12px; color: #86909c; font-weight: 600; }
.rd-cond { display: flex; flex-direction: column; gap: 6px; border-top: 1px dashed #f2f3f5; padding-top: 8px; margin-top: 6px; }
.rd-when { font-size: 12px; color: #86909c; width: 34px; flex-shrink: 0; }
.rd-offset { font-size: 11px; color: #86909c; white-space: nowrap; }
.rd-preview { background: #f7f8fa; border-radius: 8px; padding: 10px; }
.rd-preview-title { font-size: 12px; color: #86909c; margin-bottom: 6px; }
.rd-preview-human { font-size: 13px; color: #4e5969; line-height: 1.7; }
.rd-preview-logic { font-size: 11px; color: #4e5969; background: #f2f3f5; border-radius: 4px; padding: 8px; white-space: pre-wrap; word-break: break-all; margin-top: 6px; line-height: 1.5; }
:deep(.and) { color: #165dff; }
:deep(.or) { color: #ff7d00; }
</style>
