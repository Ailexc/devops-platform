<template>
  <div class="flow-ai-panel">
    <div class="panel-header">
      <div class="panel-title">
        <el-icon class="ai-icon"><MagicStick /></el-icon>
        <span>AI 智能助理</span>
      </div>
      <el-button size="small" text type="primary" @click="openConfig">
        <el-icon><Setting /></el-icon>
        配置
      </el-button>
    </div>

    <!-- 快捷指令 -->
    <div class="quick-prompts">
      <div class="quick-label">快捷指令</div>
      <div class="quick-list">
        <el-tag
          v-for="p in quickPrompts"
          :key="p.label"
          class="quick-tag"
          effect="plain"
          @click="prompt = p.prompt"
        >
          {{ p.label }}
        </el-tag>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div class="chat-area" ref="chatAreaRef">
      <!-- 欢迎消息 -->
      <div class="chat-message assistant" v-if="!messages.length">
        <div class="message-avatar">
          <el-icon><MagicStick /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-text">你好！我是 AI 流程设计助手。描述你想要的审批流程，我来帮你生成。</div>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, idx) in messages" :key="idx" class="chat-message" :class="msg.role">
        <div class="message-avatar">
          <el-icon v-if="msg.role === 'assistant'"><MagicStick /></el-icon>
          <span v-else>我</span>
        </div>
        <div class="message-content">
          <!-- 思考过程 -->
          <div v-if="msg.thinking" class="thinking-block">
            <div class="thinking-header" @click="msg.showThinking = !msg.showThinking">
              <el-icon class="thinking-icon"><Loading v-if="msg.isThinking" /><Finished v-else /></el-icon>
              <span>{{ msg.isThinking ? '思考中...' : '思考过程' }}</span>
              <el-icon class="expand-icon"><ArrowDown v-if="!msg.showThinking" /><ArrowUp v-else /></el-icon>
            </div>
            <div v-if="msg.showThinking" class="thinking-content">
              <pre>{{ msg.thinking }}</pre>
            </div>
          </div>
          
          <!-- 最终内容 -->
          <div v-if="msg.content" class="message-text">
            <pre>{{ msg.content }}</pre>
          </div>
          
          <!-- 加载状态 -->
          <div v-if="msg.isLoading && !msg.content" class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果预览 -->
    <div v-if="result" class="result-area">
      <div class="result-header">
        <el-icon class="success-icon"><CircleCheck /></el-icon>
        <span>生成完成</span>
      </div>
      <div class="result-info">
        <span>流程名称: <strong>{{ result.flow_def?.workFlowDef?.name || '未命名' }}</strong></span>
        <span>节点数: <strong>{{ countNodes(result.flow_def?.nodeConfig) }}</strong></span>
      </div>
      <div class="result-actions">
        <el-button type="primary" size="small" @click="applyResult">
          <el-icon><Check /></el-icon>
          应用到流程
        </el-button>
        <el-button size="small" @click="resetChat">重新生成</el-button>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <el-input
        v-model="prompt"
        type="textarea"
        :rows="3"
        placeholder="描述你要生成的审批流程..."
        :disabled="generating"
        @keydown.enter.ctrl="handleGenerate"
      />
      <div class="input-actions">
        <span class="input-tip">Ctrl + Enter 发送</span>
        <el-button
          type="primary"
          :loading="generating"
          :disabled="!prompt.trim() || generating"
          @click="handleGenerate"
        >
          <el-icon v-if="!generating"><Promotion /></el-icon>
          {{ generating ? '生成中...' : '生成流程' }}
        </el-button>
      </div>
    </div>

    <!-- AI 配置弹窗 -->
    <el-dialog v-model="configVisible" title="AI 模型配置" width="720px" append-to-body>
      <AiConfigPanel @update="onConfigUpdated" />
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { 
  MagicStick, Setting, Promotion, Check, Document,
  Loading, Finished, ArrowDown, ArrowUp, CircleCheck
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { AI_PROVIDERS } from '@/api/modules/ai'
import { streamGenerateFlow } from '@/api/modules/ai-stream'
import AiConfigPanel from '@/components/form/AiConfigPanel.vue'

const props = defineProps({
  currentDefinition: { type: Object, default: () => null },
  formSchema: { type: Object, default: () => ({ rules: [], options: {} }) },
})

const emit = defineEmits(['apply'])

const prompt = ref('')
const generating = ref(false)
const result = ref(null)
const configVisible = ref(false)
const messages = ref([])
const chatAreaRef = ref(null)

const quickPrompts = [
  { label: '服务器申请', prompt: '创建服务器申请流程：申请人填写主机名、CPU、内存、操作系统、预算金额 → 部门主管审批 →（金额超过 1 万需 CFO 审批）→ 运维自动开通 → 抄送申请人通知结果。' },
  { label: '请假审批', prompt: '创建一个请假审批流程：发起人提交 → 部门经理审批 → HR 审批 → 结束。超过 3 天需要总监加签。' },
  { label: '费用报销', prompt: '创建费用报销流程：发起人提交 → 直属主管审批 → 财务审核 → 出纳打款。金额超过 5000 需要部门总监审批。' },
  { label: '采购审批', prompt: '创建采购审批流程：发起人提交 → 部门经理审批 → 采购部审核 → 财务审批 → 合同签订。超过 10 万需要总经理审批。' },
  { label: '权限开通', prompt: '创建权限开通流程：申请人填写系统名称、权限类型、理由 → 主管审批 → 运维办理开通 → 完成通知。' },
  { label: '入职流程', prompt: '创建新员工入职流程：HR 发起 → 部门负责人确认 → IT 开通账号 → 行政准备工位 → 完成。' },
]

const countNodes = (nodeConfig) => {
  if (!nodeConfig) return 0
  let count = 1
  if (nodeConfig.childNode) count += countNodes(nodeConfig.childNode)
  if (nodeConfig.conditionNodes) {
    nodeConfig.conditionNodes.forEach(n => count += countNodes(n))
  }
  return count
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

const handleGenerate = async () => {
  if (!prompt.value.trim() || generating.value) return

  // 添加用户消息
  messages.value.push({ role: 'user', content: prompt.value })
  
  // 添加助手消息占位
  const assistantMsg = {
    role: 'assistant',
    thinking: '',
    content: '',
    showThinking: true,
    isThinking: true,
    isLoading: true,
  }
  messages.value.push(assistantMsg)
  
  generating.value = true
  result.value = null
  scrollToBottom()

  await streamGenerateFlow(
    {
      prompt: prompt.value.trim(),
      provider: 'xiaomi',
      current_form: props.formSchema,
    },
    {
      onThinking: (content) => {
        assistantMsg.thinking += content
        assistantMsg.isThinking = true
        scrollToBottom()
      },
      onChunk: (content) => {
        assistantMsg.content += content
        assistantMsg.isThinking = false
        assistantMsg.isLoading = false
        scrollToBottom()
      },
      onComplete: (flowDef) => {
        result.value = { flow_def: flowDef }
        assistantMsg.isLoading = false
        assistantMsg.isThinking = false
        generating.value = false
        ElMessage.success('流程生成成功')
        scrollToBottom()
      },
      onError: (error) => {
        assistantMsg.content = `❌ 生成失败: ${error}`
        assistantMsg.isLoading = false
        assistantMsg.isThinking = false
        generating.value = false
        ElMessage.error(`AI 生成失败：${error}`)
      },
    }
  )
  
  prompt.value = ''
}

const applyResult = () => {
  if (!result.value?.flow_def) return
  emit('apply', result.value.flow_def)
}

const resetChat = () => {
  messages.value = []
  result.value = null
}

const openConfig = () => { configVisible.value = true }
const onConfigUpdated = () => {}
</script>

<style scoped lang="scss">
.flow-ai-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 0;

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 20px;
    border-bottom: 1px solid #ebeef5;

    .panel-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 15px;
      font-weight: 600;
      color: #303133;

      .ai-icon { color: #409eff; font-size: 18px; }
    }
  }

  .quick-prompts {
    padding: 12px 20px;
    border-bottom: 1px solid #ebeef5;

    .quick-label {
      font-size: 12px;
      color: #909399;
      margin-bottom: 8px;
    }

    .quick-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;

      .quick-tag {
        cursor: pointer;
        transition: all 0.2s;
        &:hover { color: #409eff; border-color: #409eff; background: #ecf5ff; }
      }
    }
  }

  .chat-area {
    flex: 1;
    overflow-y: auto;
    padding: 16px 20px;
    min-height: 200px;
    max-height: 400px;
    background: #fafafa;
  }

  .chat-message {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;

    &.user {
      flex-direction: row-reverse;
      
      .message-avatar {
        background: #409eff;
        color: white;
      }
      
      .message-content {
        background: #409eff;
        color: white;
        border-radius: 12px 0 12px 12px;
        
        pre { color: white; }
      }
    }

    &.assistant {
      .message-avatar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
      }
      
      .message-content {
        background: white;
        border: 1px solid #e4e7ed;
        border-radius: 0 12px 12px 12px;
      }
    }

    .message-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 600;
      flex-shrink: 0;
    }

    .message-content {
      max-width: 85%;
      padding: 12px 16px;

      .message-text {
        pre {
          margin: 0;
          font-family: 'Monaco', 'Menlo', monospace;
          font-size: 13px;
          line-height: 1.6;
          white-space: pre-wrap;
          word-break: break-all;
          color: #303133;
        }
      }
    }
  }

  .thinking-block {
    margin-bottom: 8px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    overflow: hidden;

    .thinking-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      background: #f5f7fa;
      cursor: pointer;
      font-size: 12px;
      color: #909399;
      user-select: none;

      &:hover { background: #ebeef5; }
      
      .thinking-icon { font-size: 14px; }
      .expand-icon { margin-left: auto; }
    }

    .thinking-content {
      padding: 12px;
      background: #fafafa;
      max-height: 150px;
      overflow-y: auto;

      pre {
        margin: 0;
        font-size: 12px;
        color: #909399;
        line-height: 1.5;
        white-space: pre-wrap;
      }
    }
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 8px 0;

    span {
      width: 8px;
      height: 8px;
      background: #c0c4cc;
      border-radius: 50%;
      animation: bounce 1.4s infinite ease-in-out;

      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
    }
  }

  @keyframes bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }

  .result-area {
    padding: 16px 20px;
    background: #f0f9eb;
    border-top: 1px solid #c2e7b0;

    .result-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-weight: 600;
      color: #67c23a;

      .success-icon { font-size: 18px; }
    }

    .result-info {
      display: flex;
      gap: 20px;
      font-size: 13px;
      color: #606266;
      margin-bottom: 12px;

      strong { color: #303133; }
    }

    .result-actions {
      display: flex;
      gap: 8px;
    }
  }

  .input-area {
    padding: 16px 20px;
    border-top: 1px solid #ebeef5;
    background: white;

    .input-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 12px;

      .input-tip {
        font-size: 12px;
        color: #c0c4cc;
      }
    }
  }
}
</style>
