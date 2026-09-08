<script setup lang="ts">
</script>

<template>
  <div class="pc-sim">
    <div class="pc-header">
      <div class="brand">
        <div class="brand-logo">PC</div>
        <div class="brand-info">
          <div class="brand-name">Permission Center</div>
          <div class="brand-sub">去中心化权限管理 · Decentralized IAM</div>
        </div>
      </div>
      <div class="status-badge">已接入</div>
    </div>

    <div class="pc-content">
      <div class="arch-section">
        <h3>🏗️ 去中心化 IAM 架构</h3>
        <div class="arch-grid">
          <div class="arch-box">
            <div class="ab-icon">🌐</div>
            <div class="ab-name">PEP</div>
            <div class="ab-desc">策略执行点<br>Traefik 网关鉴权</div>
          </div>
          <div class="arch-box">
            <div class="ab-icon">🧠</div>
            <div class="ab-name">PDP</div>
            <div class="ab-desc">策略决策点<br>Casbin + OpenFGA</div>
          </div>
          <div class="arch-box">
            <div class="ab-icon">📋</div>
            <div class="ab-name">PAP</div>
            <div class="ab-desc">策略管理点<br>审批即策略</div>
          </div>
          <div class="arch-box">
            <div class="ab-icon">🔍</div>
            <div class="ab-name">PIP</div>
            <div class="ab-desc">策略信息点<br>身份解析</div>
          </div>
        </div>
      </div>

      <div class="flow-section">
        <h3>📦 权限申请流程</h3>
        <div class="flow-steps">
          <div class="flow-step">
            <div class="step-header">
              <span class="step-icon">1️⃣</span>
              <span class="step-name">应用注册</span>
            </div>
            <div class="step-desc">
              <p>应用负责人在权限中心注册应用，声明需要保护的 API 接口</p>
              <div class="step-tags">
                <span class="tag">API 声明</span>
                <span class="tag">接口分组</span>
                <span class="tag">数据模型</span>
              </div>
            </div>
          </div>
          <div class="flow-arrow">↓</div>
          <div class="flow-step">
            <div class="step-header">
              <span class="step-icon">2️⃣</span>
              <span class="step-name">发布能力包</span>
            </div>
            <div class="step-desc">
              <p>将相关接口打包为能力包（如「主机监控」），配置预设权限和可申请范围</p>
              <div class="step-tags">
                <span class="tag">能力打包</span>
                <span class="tag">预设配置</span>
                <span class="tag">范围控制</span>
              </div>
            </div>
          </div>
          <div class="flow-arrow">↓</div>
          <div class="flow-step">
            <div class="step-header">
              <span class="step-icon">3️⃣</span>
              <span class="step-name">用户申请</span>
            </div>
            <div class="step-desc">
              <p>用户在能力市场浏览可用能力包，选择预设并提交申请，填写使用理由</p>
              <div class="step-tags">
                <span class="tag">能力市场</span>
                <span class="tag">预设选择</span>
                <span class="tag">申请审批</span>
              </div>
            </div>
          </div>
          <div class="flow-arrow">↓</div>
          <div class="flow-step">
            <div class="step-header">
              <span class="step-icon">4️⃣</span>
              <span class="step-name">审批授权</span>
            </div>
            <div class="step-desc">
              <p>应用 Owner 审批申请，通过后策略立即生效，用户获得相应权限</p>
              <div class="step-tags">
                <span class="tag">审批流</span>
                <span class="tag">策略生效</span>
                <span class="tag">权限回收</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="integration-section">
        <h3>🔗 Cloud Manager 已集成</h3>
        <div class="integration-list">
          <div class="integration-item">
            <span class="int-icon">✅</span>
            <span class="int-text">能力包注册：资源管理、工单操作、成本查看</span>
          </div>
          <div class="integration-item">
            <span class="int-icon">✅</span>
            <span class="int-text">策略执行：API 网关统一鉴权</span>
          </div>
          <div class="integration-item">
            <span class="int-icon">✅</span>
            <span class="int-text">审计日志：操作记录上报</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pc-sim {
  height: 100%;
  background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%);
  padding: 20px;
  overflow-y: auto;
}

.pc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-logo {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
}

.brand-sub {
  font-size: 11px;
  color: #94a3b8;
}

.status-badge {
  padding: 4px 12px;
  background: #d1fae5;
  color: #059669;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.pc-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.arch-section, .flow-section, .integration-section {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin: 0 0 14px 0;
}

.arch-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}

.arch-box {
  padding: 12px 8px;
  background: #f8fafc;
  border-radius: 10px;
  text-align: center;
}

.ab-icon { font-size: 20px; margin-bottom: 4px; }
.ab-name { font-size: 13px; font-weight: 700; color: #1a1a2e; }
.ab-desc { font-size: 10px; color: #64748b; margin-top: 4px; line-height: 1.4; }

.flow-steps {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.flow-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  min-width: 100px;
}

.step-icon { font-size: 16px; }

.step-name {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a2e;
}

.step-desc {
  flex: 1;
}

.step-desc p {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 0 0 6px 0;
}

.step-tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  padding: 2px 6px;
  background: #eef2ff;
  color: #667eea;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.flow-arrow {
  font-size: 14px;
  color: #cbd5e1;
  text-align: center;
  padding-left: 40px;
}

.integration-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.integration-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f0fdf4;
  border-radius: 6px;
  font-size: 12px;
  color: #166534;
}

.int-icon { font-size: 14px; }
</style>
