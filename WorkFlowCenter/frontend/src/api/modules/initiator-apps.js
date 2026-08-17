import request from '../request'

// 获取发起程序列表
export function getInitiatorApps(params) {
  return request.get('/initiator-apps', { params })
}

// 创建发起程序（创建成功返回一次 API Key 明文）
export function createInitiatorApp(data) {
  return request.post('/initiator-apps', data)
}

// 更新发起程序
export function updateInitiatorApp(id, data) {
  return request.put(`/initiator-apps/${id}`, data)
}

// 删除发起程序
export function deleteInitiatorApp(id) {
  return request.delete(`/initiator-apps/${id}`)
}

// 重置 API Key（返回一次明文）
export function resetInitiatorAppKey(id) {
  return request.post(`/initiator-apps/${id}/reset-key`)
}

// 开放 API 调用统计
export function getInitiatorAppStats() {
  return request.get('/initiator-apps/stats')
}
