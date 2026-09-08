<template>
  <div class="flow-check-sim">
    <div class="page-header">
      <div class="page-header-left">
        <div class="page-header-icon"><span>🔍</span></div>
        <div>
          <h1>流程检查</h1>
          <p class="page-header-desc">服务器申请 · 发布前质量检查</p>
        </div>
      </div>
      <button class="btn-primary-sm">重新检查</button>
    </div>

    <!-- 检查概览 -->
    <div class="check-overview">
      <div class="overview-icon success">✅</div>
      <div class="overview-info">
        <div class="overview-title">检查通过，可以发布</div>
        <div class="overview-desc">共 18 项检查，16 项通过，2 项警告</div>
      </div>
      <div class="overview-stats">
        <div class="stat-item"><span class="stat-value total">18</span><span class="stat-label">检查项</span></div>
        <div class="stat-item success"><span class="stat-value">16</span><span class="stat-label">通过</span></div>
        <div class="stat-item warning"><span class="stat-value">2</span><span class="stat-label">警告</span></div>
        <div class="stat-item danger"><span class="stat-value">0</span><span class="stat-label">错误</span></div>
      </div>
    </div>

    <!-- 检查分类 -->
    <div class="check-categories">
      <div class="category" v-for="cat in categories" :key="cat.name">
        <div class="category-header" @click="cat.expanded = !cat.expanded">
          <span class="cat-icon">{{ cat.icon }}</span>
          <span class="cat-name">{{ cat.name }}</span>
          <span :class="['cat-status', cat.passed ? 'passed' : 'warning']">{{ cat.passed ? '✓ 通过' : '⚠ 警告' }}</span>
          <span class="cat-arrow">{{ cat.expanded ? '▼' : '▶' }}</span>
        </div>
        <div class="category-body" v-if="cat.expanded">
          <div class="check-item" v-for="item in cat.checks" :key="item.name" :class="'status-' + item.status">
            <span class="check-icon">{{ item.status === 'passed' ? '✅' : item.status === 'warning' ? '⚠️' : '❌' }}</span>
            <span class="check-name">{{ item.name }}</span>
            <span class="check-message">{{ item.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 发布按钮 -->
    <div class="publish-bar">
      <span class="publish-tip">检查通过后即可发布上线</span>
      <button class="btn-publish">🚀 发布流程</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

defineProps<{ focus?: string }>()

const categories = reactive([
  {
    name: '节点完整性检查', icon: '📋', passed: true, expanded: true,
    checks: [
      { name: '开始节点', status: 'passed', message: '存在且配置正确' },
      { name: '结束节点', status: 'passed', message: '存在且配置正确' },
      { name: '审批节点', status: 'passed', message: '审批人已配置' },
      { name: '办理节点', status: 'passed', message: '能力已绑定' },
    ],
  },
  {
    name: '表单字段引用检查', icon: '📝', passed: true, expanded: false,
    checks: [
      { name: '审批人字段', status: 'passed', message: '引用的表单字段存在' },
      { name: '条件表达式字段', status: 'passed', message: '字段类型匹配' },
    ],
  },
  {
    name: '流程连通性检查', icon: '🔗', passed: true, expanded: false,
    checks: [
      { name: '主流程连通', status: 'passed', message: '从开始到结束存在完整路径' },
      { name: '分支可达性', status: 'passed', message: '所有分支均可到达结束节点' },
      { name: '死循环检测', status: 'passed', message: '未发现循环路径' },
    ],
  },
  {
    name: '权限与范围检查', icon: '🔒', passed: true, expanded: false,
    checks: [
      { name: '发起人范围', status: 'passed', message: '已配置发起人范围' },
      { name: '审批人权限', status: 'passed', message: '审批人存在有效角色' },
    ],
  },
  {
    name: '超时与异常处理', icon: '⏰', passed: false, expanded: true,
    checks: [
      { name: '审批超时设置', status: 'warning', message: '建议设置超时处理策略，避免流程长时间挂起' },
      { name: '异常回调配置', status: 'warning', message: '未配置异常回调，失败后需手动处理' },
    ],
  },
  {
    name: '命名规范检查', icon: '📐', passed: true, expanded: false,
    checks: [
      { name: '流程标识规范', status: 'passed', message: '符合 snake_case 规范' },
      { name: '节点命名规范', status: 'passed', message: '所有节点均有明确命名' },
    ],
  },
])
</script>

<style scoped lang="scss">
.flow-check-sim { width: 100%; height: 100%; background: #f5f7fa; overflow-y: auto; display: flex; flex-direction: column; }

.page-header {
  display: flex; align-items: center; justify-content: space-between; background: #fff;
  border-bottom: 1px solid #e5e6eb; padding: 14px 24px; flex-shrink: 0;
}
.page-header-left { display: flex; align-items: center; gap: 12px; }
.page-header-icon {
  width: 36px; height: 36px; border-radius: 10px; background: #f0f9eb;
  display: flex; align-items: center; justify-content: center; font-size: 18px;
}
.page-header h1 { font-size: 17px; font-weight: 600; color: #1d2129; margin: 0; }
.page-header-desc { font-size: 12px; color: #86909c; margin: 1px 0 0; }
.btn-primary-sm {
  padding: 6px 14px; background: #409eff; color: #fff; border: none;
  border-radius: 6px; font-size: 12px; cursor: pointer;
}

.check-overview {
  display: flex; align-items: center; gap: 16px; margin: 16px 24px 0;
  background: #fff; border-radius: 10px; padding: 16px 20px; border: 1px solid #f2f3f5;
}
.overview-icon { font-size: 32px; }
.overview-title { font-size: 15px; font-weight: 600; color: #1d2129; }
.overview-desc { font-size: 12px; color: #86909c; margin-top: 2px; }
.overview-stats { display: flex; gap: 20px; margin-left: auto; }
.stat-item { text-align: center; }
.stat-value { display: block; font-size: 18px; font-weight: 700; }
.stat-label { font-size: 11px; color: #86909c; }
.stat-value.total { color: #1d2129; }
.stat-item.success .stat-value { color: #67c23a; }
.stat-item.warning .stat-value { color: #e6a23c; }
.stat-item.danger .stat-value { color: #f56c6c; }

.check-categories { padding: 12px 24px; flex: 1; }
.category { background: #fff; border: 1px solid #f2f3f5; border-radius: 10px; margin-bottom: 8px; overflow: hidden; }
.category-header {
  display: flex; align-items: center; gap: 10px; padding: 12px 16px; cursor: pointer;
  &:hover { background: #fafbfc; }
}
.cat-icon { font-size: 16px; }
.cat-name { font-size: 13px; font-weight: 600; color: #1d2129; flex: 1; }
.cat-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; }
.cat-status.passed { background: #f0f9eb; color: #67c23a; }
.cat-status.warning { background: #fdf6ec; color: #e6a23c; }
.cat-arrow { font-size: 10px; color: #c0c4cc; }

.category-body { padding: 0 16px 12px; }
.check-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border-radius: 6px; font-size: 12px; &:hover { background: #f7f9fc; }
}
.check-icon { font-size: 14px; }
.check-name { font-weight: 500; color: #1d2129; min-width: 100px; }
.check-message { color: #86909c; }
.status-warning .check-message { color: #e6a23c; }

.publish-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px; background: #fff; border-top: 1px solid #e5e6eb; flex-shrink: 0;
}
.publish-tip { font-size: 12px; color: #86909c; }
.btn-publish {
  padding: 8px 24px; background: #67c23a; color: #fff; border: none;
  border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer;
  &:hover { background: #5daf34; }
}
</style>
