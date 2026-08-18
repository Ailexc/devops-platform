<script setup lang="ts">
</script>

<template>
  <div class="suggest-sim">
    <div class="list-header">
      <h2>💡 优化建议</h2>
      <div class="summary-badge">预计可节省 ¥8,500/月 (23%)</div>
    </div>

    <div class="suggest-list">
      <div class="suggest-card">
        <div class="suggest-icon">🔄</div>
        <div class="suggest-content">
          <div class="suggest-title">闲置资源回收</div>
          <div class="suggest-desc">检测到 3 台主机近30天 CPU 使用率低于 5%，建议释放或降配</div>
          <div class="suggest-resources">
            <span class="resource-tag">web-server-03</span>
            <span class="resource-tag">test-server-01</span>
            <span class="resource-tag">dev-server-02</span>
          </div>
        </div>
        <div class="suggest-saving">
          <div class="saving-value">¥3,200/月</div>
          <div class="saving-percent">-12%</div>
        </div>
      </div>

      <div class="suggest-card">
        <div class="suggest-icon">📉</div>
        <div class="suggest-content">
          <div class="suggest-title">规格降配</div>
          <div class="suggest-desc">2 台 8C16G 主机实际使用不超过 4C8G，建议降配</div>
          <div class="suggest-resources">
            <span class="resource-tag">api-server-01</span>
            <span class="resource-tag">api-server-02</span>
          </div>
        </div>
        <div class="suggest-saving">
          <div class="saving-value">¥2,800/月</div>
          <div class="saving-percent">-8%</div>
        </div>
      </div>

      <div class="suggest-card">
        <div class="suggest-icon">💰</div>
        <div class="suggest-content">
          <div class="suggest-title">预留实例推荐</div>
          <div class="suggest-desc">5 台长期运行主机适合购买预留实例，享受折扣</div>
          <div class="suggest-resources">
            <span class="resource-tag">db-master-01</span>
            <span class="resource-tag">db-slave-01</span>
            <span class="resource-tag">+3 台</span>
          </div>
        </div>
        <div class="suggest-saving">
          <div class="saving-value">¥2,500/月</div>
          <div class="saving-percent">-3%</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.suggest-sim {
  padding: 20px;
  background: #f8fafc;
  height: 100%;
  overflow-y: auto;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

h2 {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.summary-badge {
  padding: 6px 12px;
  background: #d1fae5;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #059669;
}

.suggest-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggest-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.suggest-icon {
  font-size: 28px;
}

.suggest-content {
  flex: 1;
}

.suggest-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.suggest-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 10px;
  line-height: 1.5;
}

.suggest-resources {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.resource-tag {
  padding: 3px 8px;
  background: #f1f5f9;
  border-radius: 4px;
  font-size: 12px;
  color: #475569;
}

.suggest-saving {
  text-align: right;
}

.saving-value {
  font-size: 16px;
  font-weight: 700;
  color: #059669;
}

.saving-percent {
  font-size: 12px;
  color: #10b981;
}
</style>
