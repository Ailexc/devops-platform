<template>
  <div class="ai-prompt-panel">
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
          <div class="message-text">你好！我是 AI 表单设计助手。描述你想要的表单，我来帮你生成。</div>
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
        <span>共生成 <strong>{{ result.form_schema?.rules?.length || 0 }}</strong> 个字段</span>
      </div>
      <div class="result-actions">
        <el-button type="primary" size="small" @click="applyResult" :disabled="!formReady">
          <el-icon><Check /></el-icon>
          应用到表单
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
        placeholder="描述你要生成的表单..."
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
          {{ generating ? '生成中...' : '生成表单' }}
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
import { ref, nextTick } from 'vue'
import { 
  MagicStick, Setting, Promotion, Check, Document,
  Loading, Finished, ArrowDown, ArrowUp, CircleCheck
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { AI_PROVIDERS } from '@/api/modules/ai'
import { streamGenerateForm } from '@/api/modules/ai-stream'
import AiConfigPanel from './AiConfigPanel.vue'

const props = defineProps({
  currentSchema: {
    type: Object,
    default: () => ({ rules: [], options: {} })
  }
})

const emit = defineEmits(['apply'])

const prompt = ref('')
const provider = ref('xiaomi')
const generating = ref(false)
const result = ref(null)
const configVisible = ref(false)
const messages = ref([])
const chatAreaRef = ref(null)

const quickPrompts = [
  { label: '请假申请', prompt: '生成一个请假申请表单，包含请假类型（事假/病假/年假）、开始日期、结束日期、请假天数、请假原因（必填）、紧急联系人电话' },
  { label: '费用报销', prompt: '生成一个费用报销表单，包含报销类型（差旅费/餐饮费/办公用品/其他）、报销金额、费用明细（多行文本）、报销事由、发票编号、报销日期' },
  { label: '采购申请', prompt: '生成一个采购申请表单，包含采购类别、物品名称、采购数量、预算金额、供应商、期望到货日期、采购原因、审批备注' },
  { label: '入职申请', prompt: '生成一个新员工入职申请表单，包含姓名、手机号、邮箱、入职部门、岗位、入职日期、期望薪资、备注' },
  { label: '反馈意见', prompt: '生成一个反馈意见表单，包含反馈类型（建议/问题/投诉）、反馈内容（必填）、联系方式、是否匿名' }
]

const formReady = ref(false)

const typeLabel = (type) => {
  const labels = {
    input: '单行文本',
    textarea: '多行文本',
    inputNumber: '数字',
    money: '金额',
    radio: '单选',
    checkbox: '多选',
    select: '下拉选择',
    date: '日期',
    time: '时间',
    switch: '开关',
    rate: '评分',
    slider: '滑动条',
    cascader: '级联选择'
  }
  return labels[type] || type || '未知'
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
  formReady.value = false
  scrollToBottom()

  await streamGenerateForm(
    {
      prompt: prompt.value.trim(),
      provider: provider.value,
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
      onComplete: (formSchema) => {
        result.value = { form_schema: formSchema }
        formReady.value = formSchema?.rules?.length > 0
        assistantMsg.isLoading = false
        assistantMsg.isThinking = false
        generating.value = false
        ElMessage.success('表单生成成功')
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
  if (!formReady.value) return
  emit('apply', result.value.form_schema)
}

const resetChat = () => {
  messages.value = []
  result.value = null
  formReady.value = false
}

const openConfig = () => { configVisible.value = true }
const onConfigUpdated = () => {}
</script>

<style scoped lang="scss">
.ai-prompt-panel {
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
