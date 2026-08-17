<template>
  <div class="interview-bank">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><el-icon><QuestionFilled /></el-icon></div>
        <div>
          <h1>面试题库</h1>
          <p class="page-header-desc">针对本系统架构、技术点与设计的面试问答题库（预留）</p>
        </div>
      </div>
    </div>

    <div class="placeholder-card">
      <div class="placeholder-icon"><el-icon :size="44"><Memo /></el-icon></div>
      <div class="placeholder-title">敬请期待</div>
      <div class="placeholder-desc">
        面试题库模块已预留，将收录围绕本系统的高频面试问答：<br />
        流程引擎如何设计？规则引擎怎么实现可配置且安全？自动办理如何编排与可观测？……
      </div>
      <el-button type="primary" plain disabled>即将上线</el-button>
    </div>
  </div>
</template>

<script setup>
import { QuestionFilled, Memo } from '@element-plus/icons-vue'
</script>

<style scoped>
.interview-bank { padding: 24px; background: #f7f8fa; min-height: 100%; max-width: 1100px; margin: 0 auto; }
.page-header { margin-bottom: 22px; }
.page-header-left { display: flex; align-items: center; gap: 14px; }
.page-header-icon { width: 44px; height: 44px; border-radius: 10px; background: linear-gradient(135deg, #722ed1, #409eff); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 22px; }
.page-header h1 { margin: 0 0 4px; font-size: 22px; color: #1d2129; }
.page-header-desc { margin: 0; font-size: 13px; color: #86909c; }

.placeholder-card { background: #fff; border: 1px dashed #c9cdd4; border-radius: 16px; padding: 60px 30px; text-align: center; }
.placeholder-icon { color: #c9cdd4; margin-bottom: 16px; }
.placeholder-title { font-size: 20px; font-weight: 600; color: #1d2129; margin-bottom: 10px; }
.placeholder-desc { font-size: 13px; color: #86909c; line-height: 1.9; margin-bottom: 22px; }
</style>
