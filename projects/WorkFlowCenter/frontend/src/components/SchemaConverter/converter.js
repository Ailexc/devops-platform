/**
 * form-create 规则与 JSON Schema 转换工具
 */

// form-create type → JSON Schema type 映射
const TYPE_MAP = {
  input: 'string',
  textarea: 'string',
  password: 'string',
  inputNumber: 'number',
  number: 'number',
  select: 'string',
  radio: 'string',
  checkbox: 'array',
  switch: 'boolean',
  datePicker: 'string',
  timePicker: 'string',
  colorPicker: 'string',
  rate: 'number',
  slider: 'number',
  upload: 'object',
  cascader: 'array',
  treeSelect: 'array',
}

/**
 * 将 form-create 规则转换为 JSON Schema
 * @param {Array} rules - form-create 规则数组
 * @returns {Object} JSON Schema 对象
 */
export function formCreateToJsonSchema(rules) {
  const schema = {
    type: 'object',
    properties: {},
    required: [],
  }

  if (!rules || !Array.isArray(rules)) return schema

  rules.forEach((rule) => {
    const field = rule.field || rule.name || rule.model
    if (!field || rule.type === 'page' || rule.type === 'divider') return

    const prop = {
      title: rule.title || rule.label || field,
    }

    const ruleType = rule.type || 'input'
    const jsonType = TYPE_MAP[ruleType] || 'string'
    prop.type = jsonType

    // 处理 select/radio/checkbox 的选项
    if (rule.options && Array.isArray(rule.options)) {
      if (ruleType === 'checkbox') {
        prop.items = {
          type: 'string',
          enum: rule.options.map((opt) => (typeof opt === 'object' ? opt.value : opt)),
        }
      } else if (ruleType === 'select' || ruleType === 'radio') {
        prop.enum = rule.options.map((opt) => (typeof opt === 'object' ? opt.value : opt))
      }
    }

    // 处理 props 中的配置
    if (rule.props) {
      if (rule.props.min !== undefined) prop.minimum = rule.props.min
      if (rule.props.max !== undefined) prop.maximum = rule.props.max
      if (rule.props.placeholder) prop.description = rule.props.placeholder
      if (rule.props.minlength !== undefined) prop.minLength = rule.props.minlength
      if (rule.props.maxlength !== undefined) prop.maxLength = rule.props.maxlength
    }

    // 处理默认值
    if (rule.value !== undefined && rule.value !== '' && rule.value !== null) {
      prop.default = rule.value
    }

    // 处理格式
    if (ruleType === 'datePicker') {
      prop.format = 'date'
    } else if (ruleType === 'timePicker') {
      prop.format = 'time'
    } else if (ruleType === 'colorPicker') {
      prop.format = 'color'
    }

    schema.properties[field] = prop

    // 处理必填验证
    const isRequired =
      rule.validate?.some((v) => v.required) ||
      rule.props?.required ||
      rule._fc_props?.required
    if (isRequired) {
      schema.required.push(field)
    }
  })

  if (schema.required.length === 0) {
    delete schema.required
  }

  return schema
}

/**
 * 从 JSON Schema 生成 form-create 规则（简化版）
 * @param {Object} schema - JSON Schema 对象
 * @returns {Array} form-create 规则数组
 */
export function jsonSchemaToFormCreate(schema) {
  if (!schema || !schema.properties) return []

  const rules = []

  for (const [field, prop] of Object.entries(schema.properties)) {
    const rule = {
      type: mapJsonTypeToFormCreate(prop.type, prop.format),
      field,
      title: prop.title || field,
      value: prop.default ?? '',
      props: {},
    }

    if (prop.description) rule.props.placeholder = prop.description
    if (prop.minimum !== undefined) rule.props.min = prop.minimum
    if (prop.maximum !== undefined) rule.props.max = prop.maximum
    if (prop.enum) {
      rule.options = prop.enum.map((v) => ({ label: String(v), value: v }))
    }

    if (schema.required?.includes(field)) {
      rule.validate = [{ required: true, message: `${prop.title || field} 不能为空` }]
    }

    rules.push(rule)
  }

  return rules
}

function mapJsonTypeToFormCreate(type, format) {
  if (format === 'date' || format === 'date-time') return 'datePicker'
  if (format === 'time') return 'timePicker'
  if (format === 'color') return 'colorPicker'

  switch (type) {
    case 'string': return 'input'
    case 'number':
    case 'integer': return 'inputNumber'
    case 'boolean': return 'switch'
    case 'array': return 'checkbox'
    default: return 'input'
  }
}
