import request from '../request'

// 获取任务列表
export function getTasks(params) {
  return request.get('/node-tasks/', { params })
}

// 获取任务详情
export function getTaskDetail(id) {
  return request.get(`/node-tasks/${id}`)
}

// 认领任务
export function claimTask(id) {
  return request.post(`/node-tasks/${id}/claim/`)
}

// 完成任务
export function completeTask(id, data) {
  return request.post(`/node-tasks/${id}/complete/`, data)
}

// 委派任务
export function delegateTask(id, data) {
  return request.post(`/node-tasks/${id}/delegate/`, data)
}

// 拒绝任务
export function rejectTask(id, data) {
  return request.post(`/node-tasks/${id}/complete/`, { ...data, result: 'reject' })
}

// 异常任务：重新执行失败的动作
export function rerunTask(id) {
  return request.post(`/node-tasks/${id}/rerun`)
}

// 退回任务
export function returnTask(id, data) {
  return request.post(`/node-tasks/${id}/complete/`, { ...data, result: 'reject' })
}

// 获取任务表单数据
export function getTaskFormData(id) {
  return request.get(`/node-tasks/${id}/`)
}

// 更新任务表单数据
export function updateTaskFormData(id, data) {
  return request.put(`/node-tasks/${id}/`, data)
}
