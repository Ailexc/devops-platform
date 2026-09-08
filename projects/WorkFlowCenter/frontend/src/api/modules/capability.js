import request from '../request'

// 获取能力列表
export function getCapabilities(params) {
  return request.get('/capabilities', { params })
}

// 获取单个能力
export function getCapability(id) {
  return request.get(`/capabilities/${id}`)
}

// 创建能力
export function createCapability(data) {
  return request.post('/capabilities', data)
}

// 更新能力
export function updateCapability(id, data) {
  return request.put(`/capabilities/${id}`, data)
}

// 删除能力
export function deleteCapability(id) {
  return request.delete(`/capabilities/${id}`)
}

// 测试执行能力
export function testCapability(id, data) {
  return request.post(`/capabilities/${id}/test`, data)
}

// 获取任务作业列表
export function getTaskJobs(params) {
  return request.get('/task-jobs', { params })
}

// 获取任务作业统计
export function getTaskJobStats() {
  return request.get('/task-jobs/stats/')
}

// 获取单个任务作业
export function getTaskJob(id) {
  return request.get(`/task-jobs/${id}`)
}

// 执行任务作业
export function executeTaskJob(id, data) {
  return request.post(`/task-jobs/${id}/execute`, data)
}

// 获取任务作业日志
export function getTaskJobLogs(id, params) {
  return request.get(`/task-jobs/${id}/logs`, { params })
}