import request from '../request'

// ==================== 事件日志 ====================
export function getEvents(params) {
  return request.get('/events', { params })
}

export function getEvent(id) {
  return request.get(`/events/${id}`)
}

// ==================== Webhook 订阅 ====================
export function getWebhooks(params) {
  return request.get('/webhook-subscriptions', { params })
}

export function getWebhook(id) {
  return request.get(`/webhook-subscriptions/${id}`)
}

export function createWebhook(data) {
  return request.post('/webhook-subscriptions', data)
}

export function updateWebhook(id, data) {
  return request.put(`/webhook-subscriptions/${id}`, data)
}

export function deleteWebhook(id) {
  return request.delete(`/webhook-subscriptions/${id}`)
}

// ==================== Webhook 投递记录 ====================
export function getWebhookDeliveries(params) {
  return request.get('/webhook-deliveries', { params })
}

// ==================== 集成健康度 ====================
export function getWebhookStats() {
  return request.get('/webhook-stats')
}

export function retryWebhookDelivery(id) {
  return request.post(`/webhook-deliveries/${id}/retry/`)
}

export default {
  getEvents,
  getEvent,
  getWebhooks,
  getWebhook,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  getWebhookDeliveries,
  getWebhookStats,
  retryWebhookDelivery,
}
