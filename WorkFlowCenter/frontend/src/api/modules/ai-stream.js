/**
 * AI 流式生成工具
 * 支持 SSE (Server-Sent Events) 实时接收 AI 生成内容
 */

/**
 * 获取认证 token
 */
function getToken() {
  return localStorage.getItem('token')
}

/**
 * 流式生成表单
 * @param {Object} params - { prompt, provider, config_id }
 * @param {Function} onChunk - 收到内容块时的回调 (content: string)
 * @param {Function} onComplete - 生成完成时的回调 (formSchema: Object)
 * @param {Function} onError - 出错时的回调 (error: string)
 */
export async function streamGenerateForm({ prompt, provider, config_id }, { onThinking, onChunk, onComplete, onError }) {
  const token = getToken()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  
  try {
    const response = await fetch(`${baseUrl}/ai/config/generate-form-stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ prompt, provider, config_id }),
    })

    console.log('[StreamAI] 响应状态:', response.status, response.headers.get('content-type'))
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('[StreamAI] 请求失败:', errorData)
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') return

        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'thinking' && parsed.content) {
            onThinking && onThinking(parsed.content)
          } else if (parsed.type === 'content' && parsed.content) {
            onChunk(parsed.content)
          } else if (parsed.type === 'result' && parsed.form_schema) {
            onComplete(parsed.form_schema)
          } else if (parsed.type === 'error') {
            onError(parsed.message)
          }
        } catch (e) {
          // 忽略解析错误
        }
      }
    }
  } catch (error) {
    onError(error.message || '请求失败')
  }
}

/**
 * 流式生成流程
 * @param {Object} params - { prompt, provider, config_id, current_form }
 * @param {Function} onChunk - 收到内容块时的回调 (content: string)
 * @param {Function} onComplete - 生成完成时的回调 (flowDef: Object)
 * @param {Function} onError - 出错时的回调 (error: string)
 */
export async function streamGenerateFlow({ prompt, provider, config_id, current_form }, { onThinking, onChunk, onComplete, onError }) {
  const token = getToken()
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  
  console.log('[StreamAI] 开始流式请求, baseUrl:', baseUrl, 'token:', token ? '存在' : '不存在')
  
  try {
    const response = await fetch(`${baseUrl}/ai/config/generate-flow-stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ prompt, provider, config_id, current_form }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') return

        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'thinking' && parsed.content) {
            onThinking && onThinking(parsed.content)
          } else if (parsed.type === 'content' && parsed.content) {
            onChunk(parsed.content)
          } else if (parsed.type === 'result' && parsed.flow_def) {
            onComplete(parsed.flow_def)
          } else if (parsed.type === 'error') {
            onError(parsed.message)
          }
        } catch (e) {
          console.error('[StreamAI] 解析错误:', e, 'data:', data)
        }
      }
    }
  } catch (error) {
    onError(error.message || '请求失败')
  }
}

export default {
  streamGenerateForm,
  streamGenerateFlow,
}
