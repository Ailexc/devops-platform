import request from '../request'

// 获取工单类型列表
export function getTicketTypes(params) {
  return request.get('/ticket-types', { params })
}

// 获取单个工单类型
export function getTicketType(id) {
  return request.get(`/ticket-types/${id}`)
}

// 创建工单类型
export function createTicketType(data) {
  return request.post('/ticket-types', data)
}

// 更新工单类型
export function updateTicketType(id, data) {
  return request.put(`/ticket-types/${id}`, data)
}

// 删除工单类型
export function deleteTicketType(id) {
  return request.delete(`/ticket-types/${id}`)
}

export default {
  getTicketTypes,
  getTicketType,
  createTicketType,
  updateTicketType,
  deleteTicketType,
}
