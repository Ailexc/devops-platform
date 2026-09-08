import request from '../request'

// 获取流程定义列表
export function getDefinitions(params) {
  return request.get('/process-definitions', { params })
}

// 获取单个流程定义
export function getDefinition(id) {
  return request.get(`/process-definitions/${id}`)
}

// 创建流程定义
export function createDefinition(data) {
  return request.post('/process-definitions', data)
}

// 更新流程定义
export function updateDefinition(id, data) {
  return request.put(`/process-definitions/${id}`, data)
}

// 删除流程定义
export function deleteDefinition(id) {
  return request.delete(`/process-definitions/${id}`)
}

// 发布流程定义
export function publishDefinition(id) {
  return request.post(`/process-definitions/${id}/publish`)
}

// 停用流程定义
export function deactivateDefinition(id) {
  return request.post(`/process-definitions/${id}/deactivate`)
}

// 检查流程配置（基于已保存的定义）
export function checkDefinition(id) {
  return request.post(`/process-definitions/${id}/check`)
}

// 校验流程配置（无需保存，用于编辑器第4步实时检查）
export function validateDefinition(data) {
  return request.post('/process-definitions/validate', data)
}

// 根据表单数据预计算审批路径（提单前预览）
export function previewPath(id, data) {
  return request.post(`/process-definitions/${id}/preview-path`, data)
}

// 获取业务规则数据源字典（供规则配置器下拉）
export function getRuleMeta(id) {
  return request.get(`/process-definitions/${id}/rule-meta`)
}

// 提单预检（基础校验 + 业务规则 + 办理节点 Dry Run）
export function previewCheck(id, data) {
  return request.post(`/process-definitions/${id}/preview-check`, data)
}

// 提交权威复检（防绕过，error 级命中拒绝提交）
export function submitCheck(id, data) {
  return request.post(`/process-definitions/${id}/submit-check`, data)
}

// 测试模块：获取可测流程与预设表单
export function getE2eMeta() {
  return request.get('/process-instances/e2e-meta/')
}

// 测试模块：某流程最近的测试场景运行记录（详情页测试记录）
export function getE2eHistory(params) {
  return request.get('/process-instances/e2e-history/', { params })
}

// 测试模块：按测试场景跑通单个流程（正常完成 / 进行中 / 异常 / 驳回）
export function runE2e(data) {
  return request.post('/process-instances/e2e-run/', data)
}

// 获取流程实例列表
export function getInstances(params) {
  return request.get('/process-instances', { params })
}

// 发起流程
export function startProcess(data) {
  return request.post('/process-instances/start/', data)
}

// 获取流程实例详情
export function getInstanceDetail(id) {
  return request.get(`/process-instances/${id}`)
}

// 获取流程实例的审批记录（含发起来源）
export function getInstanceApprovalRecords(id) {
  return request.get(`/process-instances/${id}/approval-records`)
}

// 获取流程实例节点运行状态与执行日志（申请详情流程追踪）
export function getInstanceFlowStatus(id) {
  return request.get(`/process-instances/${id}/flow-status`)
}

// 获取流程时间线
export function getTimeline(instanceId) {
  return request.get(`/process-instances/${instanceId}/timeline`)
}

// 撤销流程实例
export function cancelInstance(id) {
  return request.post(`/process-instances/${id}/cancel`)
}
