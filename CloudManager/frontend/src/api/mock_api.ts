/**
 * Mock 数据 API 模块
 * 用于调用后端的 Mock 数据接口
 */
import api from './request'

// ===== 部门 API =====
export const mockDepartmentApi = {
  list() {
    return api.get<any[]>('/mock/departments/')
  },
  tree() {
    return api.get<any[]>('/mock/departments/tree/')
  },
}

// ===== 应用 API =====
export const mockApplicationApi = {
  list(params?: { department_id?: number }) {
    return api.get<any[]>('/mock/applications/', { params })
  },
  detail(id: number) {
    return api.get<any>(`/mock/applications/${id}/`)
  },
}

// ===== 环境 API =====
export const mockEnvironmentApi = {
  list(params?: { application_id?: number }) {
    return api.get<any[]>('/mock/environments/', { params })
  },
  detail(id: number) {
    return api.get<any>(`/mock/environments/${id}/`)
  },
}

// ===== 服务 API =====
export const mockServiceApi = {
  list(params?: { environment_id?: number }) {
    return api.get<any[]>('/mock/services/', { params })
  },
  detail(id: number) {
    return api.get<any>(`/mock/services/${id}/`)
  },
  dependencies(id: number) {
    return api.get<any[]>(`/mock/services/${id}/dependencies/`)
  },
}

// ===== 关系 API =====
export const mockRelationApi = {
  list(params?: { environment_id?: number }) {
    return api.get<any[]>('/mock/relations/', { params })
  },
  detail(id: number) {
    return api.get<any>(`/mock/relations/${id}/`)
  },
  create(data: any) {
    return api.post<any>('/mock/relations/create/', data)
  },
  update(id: number, data: any) {
    return api.put<any>(`/mock/relations/${id}/update/`, data)
  },
  delete(id: number) {
    return api.delete(`/mock/relations/${id}/delete/`)
  },
}

// ===== 图谱 API =====
export const mockGraphApi = {
  environment(envId: number) {
    return api.get<any>(`/mock/graph/environment/${envId}/`)
  },
  application(appId: number, environmentId?: number) {
    const params = environmentId ? { environment_id: environmentId } : {}
    return api.get<any>(`/mock/graph/application/${appId}/`, { params })
  },
}

// ===== 资源 API =====
export const mockResourceApi = {
  list(params?: { environment_id?: number; resource_type?: string }) {
    return api.get<any[]>('/mock/resources/', { params })
  },
}

// ===== 部署单元 API =====
export const mockDeploymentUnitApi = {
  list(params?: { environment_id?: number }) {
    return api.get<any[]>('/mock/deployment-units/', { params })
  },
}

// ===== 变更记录 API =====
export const mockChangeRecordApi = {
  list(params?: { ticket_no?: string }) {
    return api.get<any[]>('/mock/change-records/', { params })
  },
  create(data: any) {
    return api.post<any>('/mock/change-records/create/', data)
  },
}

// ===== 统计 API =====
export const mockStatisticsApi = {
  get() {
    return api.get<any>('/mock/statistics/')
  },
}

// ===== 初始化 API =====
export const mockInitializeApi = {
  run() {
    return api.post<any>('/mock/initialize/')
  },
}