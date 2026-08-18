<script setup lang="ts">
</script>

<template>
  <div class="budget-sim">
    <div class="list-header">
      <h2>📊 预算管理</h2>
    </div>

    <div class="budget-grid">
      <div class="budget-card">
        <div class="budget-header">
          <span class="dept">研发一部</span>
          <span class="status over">超支</span>
        </div>
        <div class="budget-bar">
          <div class="bar-fill over" style="width: 112%;"></div>
        </div>
        <div class="budget-info">
          <span>已用: ¥28,000</span>
          <span>预算: ¥25,000</span>
        </div>
        <div class="budget-alert">⚠️ 超出预算 12%</div>
      </div>

      <div class="budget-card">
        <div class="budget-header">
          <span class="dept">研发二部</span>
          <span class="status normal">正常</span>
        </div>
        <div class="budget-bar">
          <div class="bar-fill normal" style="width: 72%;"></div>
        </div>
        <div class="budget-info">
          <span>已用: ¥18,000</span>
          <span>预算: ¥25,000</span>
        </div>
      </div>

      <div class="budget-card">
        <div class="budget-header">
          <span class="dept">运维部</span>
          <span class="status warning">预警</span>
        </div>
        <div class="budget-bar">
          <div class="bar-fill warning" style="width: 88%;"></div>
        </div>
        <div class="budget-info">
          <span>已用: ¥22,000</span>
          <span>预算: ¥25,000</span>
        </div>
        <div class="budget-alert warning">⚠️ 已用 88%，即将超支</div>
      </div>

      <div class="budget-card">
        <div class="budget-header">
          <span class="dept">测试部</span>
          <span class="status normal">正常</span>
        </div>
        <div class="budget-bar">
          <div class="bar-fill normal" style="width: 45%;"></div>
        </div>
        <div class="budget-info">
          <span>已用: ¥9,000</span>
          <span>预算: ¥20,000</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.budget-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  margin-bottom: 20px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.budget-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.budget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.dept {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
}

.status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.status.normal { background: #d1fae5; color: #059669; }
.status.warning { background: #fef3c7; color: #d97706; }
.status.over { background: #fee2e2; color: #dc2626; }

.budget-bar {
  height: 10px;
  background: #f1f5f9;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 10px;
}

.bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease;
}

.bar-fill.normal { background: #10b981; }
.bar-fill.warning { background: #f59e0b; }
.bar-fill.over { background: #ef4444; }

.budget-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #64748b;
}

.budget-alert {
  margin-top: 8px;
  padding: 6px 10px;
  background: #fee2e2;
  border-radius: 6px;
  font-size: 12px;
  color: #dc2626;
}

.budget-alert.warning {
  background: #fef3c7;
  color: #d97706;
}
</style>
