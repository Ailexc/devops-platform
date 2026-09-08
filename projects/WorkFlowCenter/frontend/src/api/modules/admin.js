import request from '../request'

// 用户管理
export function getUsers(params) {
  return request.get('/users', { params })
}

export function getUser(id) {
  return request.get(`/users/${id}`)
}

export function createUser(data) {
  return request.post('/users', data)
}

export function updateUser(id, data) {
  // 用 PATCH 部分更新：状态切换只传 is_active，编辑传部分字段，避免 PUT 全量缺字段 400
  return request.patch(`/users/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/users/${id}`)
}

// 部门管理
export function getDepartments(params) {
  return request.get('/departments', { params })
}

export function getDepartment(id) {
  return request.get(`/departments/${id}`)
}

export function createDepartment(data) {
  return request.post('/departments', data)
}

export function updateDepartment(id, data) {
  return request.put(`/departments/${id}`, data)
}

export function deleteDepartment(id) {
  return request.delete(`/departments/${id}`)
}

// 角色管理
export function getRoles(params) {
  return request.get('/roles', { params })
}

export function getRole(id) {
  return request.get(`/roles/${id}`)
}

export function createRole(data) {
  return request.post('/roles', data)
}

export function updateRole(id, data) {
  return request.put(`/roles/${id}`, data)
}

export function deleteRole(id) {
  return request.delete(`/roles/${id}`)
}