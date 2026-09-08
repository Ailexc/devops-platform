/**
 * form-create 规则 → Beeflow 流程设计器 flowWidgets 适配层
 *
 * Beeflow 流程设计器只消费表单控件的元数据（name / label / type / options / required），
 * 用于条件分支、节点表单权限与流程校验。type 为其 FlowConstant 中的 WIDGET 枚举。
 */
import { WIDGET } from '@/components/flow/common/FlowConstant'

// form-create 控件类型 → Beeflow WIDGET 枚举
const TYPE_MAP = {
  input: WIDGET.SINGLELINE_TEXT, // 单行文本 0
  textarea: WIDGET.MULTILINE_TEXT, // 多行文本 1
  number: WIDGET.NUMBER, // 数字 3
  inputNumber: WIDGET.NUMBER, // 数字 3
  money: WIDGET.MONEY, // 金额 4
  select: WIDGET.SINGLE_CHOICE, // 单选 5
  radio: WIDGET.SINGLE_CHOICE, // 单选 5
  checkbox: WIDGET.MULTI_CHOICE, // 多选 6
  datePicker: WIDGET.DATE, // 日期 7
  timePicker: WIDGET.DATE, // 时间（近似日期）7
  upload: WIDGET.ATTACHMENT, // 附件 11
  cascader: WIDGET.SINGLE_CHOICE, // 级联（近似单选）5
  rate: WIDGET.RATE, // 评分 21
}

/**
 * 判断 form-create 控件是否支持作为流程条件字段
 */
export function isConditionWidget(type) {
  return TYPE_MAP[type] !== undefined
}

/**
 * 将 form-create 规则数组转换为 Beeflow flowWidgets
 * @param {Array} rules - form-create 规则（rule.field / rule.title / rule.type / rule.options / rule.validate / rule.props）
 * @returns {Array} flowWidgets
 */
export function formCreateToFlowWidgets(rules = []) {
  const widgets = []
  if (!Array.isArray(rules)) return widgets

  rules.forEach((rule) => {
    const field = rule.field || rule.name || rule.model
    if (!field) return
    if (['page', 'divider', 'grid', 'row', 'col'].includes(rule.type)) return

    const ruleType = rule.type || 'input'
    const widgetType = TYPE_MAP[ruleType]
    if (widgetType === undefined) return // 无法映射的控件不进入流程条件/权限体系

    const isRangeDate = ruleType === 'datePicker' && ['daterange', 'monthrange'].includes(rule.props?.type)
    const isMultipleSelect = ruleType === 'select' && (rule.props?.multiple || rule.props?.multipleLimit)

    const widget = {
      name: field,
      label: rule.title || rule.label || field,
      type: isRangeDate ? WIDGET.DATE_RANGE : isMultipleSelect ? WIDGET.MULTI_CHOICE : widgetType,
      required: !!(rule.validate?.some((v) => v.required) || rule.props?.required),
      options: Array.isArray(rule.options) ? rule.options : [],
    }
    widgets.push(widget)
  })

  return widgets
}

export default { formCreateToFlowWidgets, isConditionWidget }
