import request from '../request'

// 获取工单列表
export function getTickets(params) {
  return request.get('/tickets', { params })
}

// 创建工单
export function createTicket(data) {
  return request.post('/tickets', data)
}

// 获取工单详情
export function getTicketDetail(id) {
  return request.get(`/tickets/${id}`)
}

// 添加工单评论
export function addComment(id, data) {
  return request.post(`/tickets/${id}/comments`, data)
}

// 获取工单评论列表
export function getComments(id, params) {
  return request.get(`/tickets/${id}/comments`, { params })
}

// 更新工单状态
export function updateTicketStatus(id, data) {
  return request.put(`/tickets/${id}/status`, data)
}

// 关闭工单
export function closeTicket(id) {
  return request.post(`/tickets/${id}/close`)
}

// 重新打开工单
export function reopenTicket(id) {
  return request.post(`/tickets/${id}/reopen`)
}