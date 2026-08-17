import request from '../request'

// 知识库文档列表（分页，仅摘要）
export function getDocs(params) {
  return request.get('/knowledge-docs', { params })
}

// 知识库文档详情（含 HTML 正文，key 标识）
export function getDoc(key) {
  return request.get(`/knowledge-docs/${key}`)
}
