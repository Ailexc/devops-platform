// 事件类型中文映射：英文唯一 ID → 人类友好中文标识
export const EVENT_TYPE_LABELS = {
  'process.started': '流程启动',
  'process.completed': '流程完成',
  'process.terminated': '流程终止',
  'process.suspended': '流程挂起',
  'process.resumed': '流程恢复',
  'task.created': '任务创建',
  'task.completed': '任务完成',
  'task.rejected': '任务驳回',
  'task.claimed': '任务签收',
  'ticket.created': '工单创建',
  'ticket.updated': '工单更新',
  'ticket.completed': '工单完成',
  'ticket.cancelled': '工单撤销',
}

// 取事件中文标识；未映射则原样返回（如自定义/静态说明）
export function eventLabel(type) {
  return EVENT_TYPE_LABELS[type] || type
}
