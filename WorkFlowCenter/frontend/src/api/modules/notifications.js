import request from '../request'

// 获取我的通知
export function getMyNotifications(params) {
  return request.get('/notifications/my/', { params })
}

// 获取通知列表
export function getNotifications(params) {
  return request.get('/notifications', { params })
}

// 标记单条已读
export function markNotificationRead(id) {
  return request.post(`/notifications/${id}/mark-read/`)
}

// 标记全部已读
export function markAllNotificationsRead() {
  return request.post('/notifications/mark-all-read/')
}

export default {
  getMyNotifications,
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
}
