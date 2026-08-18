<script setup lang="ts">
</script>

<template>
  <div class="arch-sim">
    <div class="arch-card">
      <h3>🏗️ 系统架构</h3>
      
      <!-- 四层架构 -->
      <div class="arch-layers">
        <div class="layer">
          <div class="layer-icon">🖥️</div>
          <div class="layer-content">
            <div class="layer-title">前端展示层</div>
            <div class="layer-desc">Vue 3 + TypeScript + Ant Design Vue</div>
            <div class="layer-detail">控制台布局 · 多页签 · Schema 驱动</div>
          </div>
        </div>
        <div class="layer-arrow">↕</div>
        <div class="layer">
          <div class="layer-icon">⚙️</div>
          <div class="layer-content">
            <div class="layer-title">后端服务层</div>
            <div class="layer-desc">Django + DRF + SimpleJWT</div>
            <div class="layer-detail">RESTful API · JWT 认证 · RBAC 权限</div>
          </div>
        </div>
        <div class="layer-arrow">↕</div>
        <div class="layer">
          <div class="layer-icon">📋</div>
          <div class="layer-content">
            <div class="layer-title">工单系统层</div>
            <div class="layer-desc">状态机 + 审批流 + 自动执行</div>
            <div class="layer-detail">8种状态 · 多级审批 · Mock Provider</div>
          </div>
        </div>
        <div class="layer-arrow">↕</div>
        <div class="layer highlight">
          <div class="layer-icon">🗄️</div>
          <div class="layer-content">
            <div class="layer-title">CMDB 数据层</div>
            <div class="layer-desc">唯一数据源 · 多态建模 · 关系图谱</div>
            <div class="layer-detail">13种资源 · 多云适配 · 依赖分析</div>
          </div>
        </div>
      </div>

      <!-- 核心能力 -->
      <div class="core-abilities">
        <h4>核心能力</h4>
        <div class="ability-grid">
          <div class="ability-item">
            <span class="ability-icon">☁️</span>
            <span class="ability-text">多云纳管</span>
          </div>
          <div class="ability-item">
            <span class="ability-icon">📋</span>
            <span class="ability-text">工单审批</span>
          </div>
          <div class="ability-item">
            <span class="ability-icon">🔗</span>
            <span class="ability-text">依赖图谱</span>
          </div>
          <div class="ability-item">
            <span class="ability-icon">💰</span>
            <span class="ability-text">成本管理</span>
          </div>
        </div>
      </div>

      <div class="arch-note">
        <span class="note-icon">✅</span>
        <span>所有数据以 CMDB 为唯一数据源，保证数据一致性</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.arch-sim {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  background: #f8fafc;
}

.arch-card {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 20px 0;
  text-align: center;
}

h4 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 16px 0 12px 0;
}

.arch-layers {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.layer {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 10px;
  transition: all 0.3s;
}

.layer.highlight {
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
  border: 2px solid #667eea;
}

.layer-icon {
  font-size: 20px;
}

.layer-content {
  flex: 1;
}

.layer-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}

.layer-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.layer-detail {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.layer-arrow {
  font-size: 14px;
  color: #cbd5e1;
}

.core-abilities {
  margin-top: 16px;
}

.ability-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.ability-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 8px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
}

.ability-icon {
  font-size: 18px;
}

.ability-text {
  font-size: 11px;
  font-weight: 500;
  color: #475569;
}

.arch-note {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 8px;
  font-size: 13px;
  color: #166534;
}

.note-icon { font-size: 16px; }
</style>
