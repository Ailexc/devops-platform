import request from '../request'

// 获取 AI 配置列表
export function getAiConfigs(params) {
  return request.get('/ai/config', { params })
}

// 创建 AI 配置
export function createAiConfig(data) {
  return request.post('/ai/config', data)
}

// 更新 AI 配置
export function updateAiConfig(id, data) {
  return request.put(`/ai/config/${id}`, data)
}

// 删除 AI 配置
export function deleteAiConfig(id) {
  return request.delete(`/ai/config/${id}`)
}

// AI 生成表单
export function generateForm(data) {
  return request.post('/ai/config/generate-form', data)
}

// AI 生成流程
export function generateFlow(data) {
  return request.post('/ai/config/generate-flow', data)
}

// 测试 AI 连接
export function testAiConnection(data) {
  return request.post('/ai/config/test', data)
}

// AI 提供商选项（与后端 AIConfig.Provider 保持一致）
export const AI_PROVIDERS = [
  { value: 'xiaomi', label: '小米 MiMo', priority: 3 },
  { value: 'openai', label: 'OpenAI', priority: 3 },
  { value: 'deepseek', label: 'DeepSeek', priority: 3 },
  { value: 'zhipu', label: '智谱 GLM', priority: 2 },
  { value: 'qwen', label: '通义千问', priority: 2 },
  { value: 'ollama', label: '本地 Ollama', priority: 1 },
]

export default {
  getAiConfigs,
  createAiConfig,
  updateAiConfig,
  deleteAiConfig,
  generateForm,
  generateFlow,
  testAiConnection,
  AI_PROVIDERS,
}
