/**
 * 业务规则元数据与工具（方案 B · 结构化 AST）
 *
 * 数据源来自后端 rule-meta 接口：{ form: [...], context: [...], operators: {...} }
 * 规则形态：
 *   { id, name, level, message, suggestion,
 *     groups: [ [{source, op, refType, fixed, refField, offset}] ] }  // 多组=或，组内=且
 */

// 操作符展示名（与后端 rules.OPERATORS 对齐）
export const OP_LABELS = {
  '>': '大于',
  '>=': '大于等于',
  '<': '小于',
  '<=': '小于等于',
  '==': '等于',
  '!=': '不等于',
  'in': '属于',
  'not_in': '不属于',
  'contains': '包含',
  'not_contains': '不包含',
  'matches': '匹配',
}

// 按数据源类型提供操作符子集
export function opsForType(type) {
  if (['number', 'money'].includes(type)) return ['>', '>=', '<', '<=', '==', '!=']
  if (type === 'enum') return ['==', '!=']
  if (type === 'array') return ['in', 'not_in']
  return ['==', '!=', 'contains', 'not_contains', 'matches']
}

export function opLabel(op) {
  return OP_LABELS[op] || op
}

// 将后端 rule-meta 数据源组装为分组结构
export function buildSourceGroups(ruleMeta) {
  const groups = []
  if (ruleMeta?.form?.length) {
    groups.push({
      name: '表单字段',
      items: ruleMeta.form.map(f => ({ ...f, provider: '表单字段' })),
    })
  }
  if (ruleMeta?.context?.length) {
    groups.push({
      name: '业务上下文指标',
      items: ruleMeta.context.map(c => ({ ...c })),
    })
  }
  return groups
}

export function findSource(groups, name) {
  for (const g of groups || []) {
    const hit = g.items.find(s => s.name === name)
    if (hit) return hit
  }
  return null
}

export function typeOf(groups, name) {
  const s = findSource(groups, name)
  return s ? s.type : 'text'
}

// ---------- 类型判断 ----------
export const isNumType = (groups, name) => ['number', 'money'].includes(typeOf(groups, name))
export const isEnumType = (groups, name) => typeOf(groups, name) === 'enum'
export const isTextType = (groups, name) => !['number', 'money', 'enum', 'array'].includes(typeOf(groups, name))

// ---------- 人话描述 ----------
function condHuman(groups, c) {
  const src = findSource(groups, c.source)
  const srcLabel = (src && src.label) || c.source
  let rhs
  if (c.refType === 'field') {
    const ref = findSource(groups, c.refField)
    rhs = (ref && ref.label) || c.refField
    const offset = Number(c.offset) || 0
    if (offset) rhs += offset > 0 ? ` − ${offset}` : ` + ${-offset}`
  } else {
    rhs = c.fixed
  }
  return `<span style="color:#1d2129">${srcLabel}</span> ${opLabel(c.op)} <span style="color:#165dff">${rhs}</span>`
}

export function groupsHuman(groups, ruleGroups) {
  return (ruleGroups || [])
    .map(g => g.map(c => condHuman(groups, c)).join('<span class="and"> 且 </span>'))
    .join('<span class="or"> 或 </span>')
}

// ---------- JSON Logic 派生（展示 / 审计用） ----------
function condRhs(c) {
  if (c.refType === 'field') {
    const ref = { var: c.refField }
    const offset = Number(c.offset) || 0
    return offset ? { '-': [ref, offset] } : ref
  }
  return typeof c.fixed === 'number' ? c.fixed : `"${c.fixed}"`
}

function condLogic(c) {
  return { [c.op]: [{ var: c.source }, condRhs(c)] }
}

export function groupsLogic(ruleGroups) {
  const andGroups = (ruleGroups || []).map(g =>
    g.length === 1 ? condLogic(g[0]) : { and: g.map(condLogic) },
  )
  return andGroups.length === 1 ? andGroups[0] : { or: andGroups }
}

export function buildLogic(rule) {
  return JSON.stringify(groupsLogic(rule.groups || []), null, 2)
}

// 新建空条件
export function newCondition(presetSource) {
  const c = {
    source: presetSource || '',
    op: '',
    refType: 'fixed',
    fixed: null,
    refField: '',
    offset: 0,
  }
  if (presetSource) c.op = opsForType(typeOf([{ items: [{ name: presetSource, type: 'number' }] }], presetSource))[0]
  return c
}
