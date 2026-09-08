<template>
  <div class="ai-config-page">
    <div class="page-header">
      <div class="page-header-left"><div class="page-header-icon"><el-icon><MagicStick /></el-icon></div><div><h1>AI 配置</h1><p class="page-header-desc">配置人工智能辅助功能</p></div></div>
      <p>管理 AI 表单生成所需的模型连接配置</p>
    </div>

    <!-- 能力说明 -->
    <el-alert
      title="AI 表单生成能力"
      type="info"
      show-icon
      :closable="false"
      class="intro-alert"
    >
      <p class="alert-desc">
        在「表单设计」步骤中点击「AI 生成」按钮，输入自然语言即可自动生成表单。
        支持小米 MiMo、OpenAI、DeepSeek、智谱 GLM、通义千问与本地 Ollama。
        未配置时默认使用小米 MiMo（可通过环境变量提供密钥）。
      </p>
    </el-alert>

    <el-card>
      <AiConfigPanel />
    </el-card>
  </div>
</template>

<script setup>
import AiConfigPanel from '@/components/form/AiConfigPanel.vue'
</script>

<style scoped lang="scss">
.ai-config-page {
  padding: 24px;
  background: var(--ticket-bg, #F7F8FA);
  min-height: 100%;
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;

  h2 {
    margin: 0 0 4px;
    color: #303133;
    font-size: 20px;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #909399;
  }
}

.intro-alert {
  margin-bottom: 20px;

  .alert-desc {
    margin: 8px 0 0;
    font-size: 13px;
    line-height: 1.6;
    color: #606266;
  }
}
</style>
