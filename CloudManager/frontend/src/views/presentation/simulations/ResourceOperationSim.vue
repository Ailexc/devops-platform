<script setup lang="ts">
</script>

<template>
  <div class="operation-sim">
    <div class="dialog-overlay">
      <div class="dialog">
        <div class="dialog-header">
          <h3>⚙️ 变更实例配置</h3>
          <span class="close-btn">×</span>
        </div>
        
        <div class="dialog-body">
          <!-- 当前配置 -->
          <div class="form-section">
            <div class="section-title">📋 当前配置</div>
            <div class="current-config">
              <div class="config-item">
                <span class="config-label">实例 ID</span>
                <span class="config-value mono">i-0a1b2c3d4e5f6g7h8</span>
              </div>
              <div class="config-item">
                <span class="config-label">当前规格</span>
                <span class="config-value">m5.xlarge (4C16G)</span>
              </div>
              <div class="config-item">
                <span class="config-label">状态</span>
                <span class="config-value"><span class="status-dot running"></span> 运行中</span>
              </div>
            </div>
          </div>

          <!-- 目标配置 -->
          <div class="form-section">
            <div class="section-title">🎯 目标配置</div>
            <div class="form-group">
              <label>目标规格 <span class="required">*</span></label>
              <div class="spec-options">
                <div class="spec-card">
                  <div class="spec-name">m5.large</div>
                  <div class="spec-spec">2C8G</div>
                  <div class="spec-price">¥0.26/时</div>
                  <div class="spec-tag down">降配 ↓</div>
                </div>
                <div class="spec-card current">
                  <div class="spec-name">m5.xlarge</div>
                  <div class="spec-spec">4C16G</div>
                  <div class="spec-price">¥0.52/时</div>
                  <div class="spec-tag current">当前</div>
                </div>
                <div class="spec-card selected">
                  <div class="spec-name">m5.2xlarge</div>
                  <div class="spec-spec">8C32G</div>
                  <div class="spec-price">¥1.04/时</div>
                  <div class="spec-tag up">升配 ↑</div>
                </div>
                <div class="spec-card">
                  <div class="spec-name">m5.4xlarge</div>
                  <div class="spec-spec">16C64G</div>
                  <div class="spec-price">¥2.08/时</div>
                  <div class="spec-tag up">升配 ↑</div>
                </div>
              </div>
            </div>
          </div>

          <!-- 变更影响 -->
          <div class="form-section">
            <div class="section-title">⚠️ 变更影响</div>
            <div class="impact-list">
              <div class="impact-item warning">
                <span class="impact-icon">⚠️</span>
                <div class="impact-content">
                  <span class="impact-title">需要重启</span>
                  <span class="impact-desc">实例将在变更期间重启，预计中断 2-5 分钟</span>
                </div>
              </div>
              <div class="impact-item info">
                <span class="impact-icon">💰</span>
                <div class="impact-content">
                  <span class="impact-title">费用变化</span>
                  <span class="impact-desc">当前 ¥0.52/时 → 目标 ¥1.04/时，月增约 ¥374</span>
                </div>
              </div>
              <div class="impact-item success">
                <span class="impact-icon">🔒</span>
                <div class="impact-content">
                  <span class="impact-title">数据安全</span>
                  <span class="impact-desc">本地存储数据不受影响，EBS 卷保持挂载</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 联动说明 -->
          <div class="form-section">
            <div class="section-title">🔗 联动能力</div>
            <div class="capability-list">
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">自动创建变更工单，进入审批流程</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">审批通过后自动执行变更操作</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">变更完成后自动更新 CMDB 记录</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">自动通知相关人员</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <span class="btn-cancel">取消</span>
          <span class="btn-submit">✅ 提交变更（将创建工单）</span>
        </div>

        <!-- 底部说明 -->
        <div class="form-note">
          💡 与直接在云控制台变更不同，这里的一次提交会自动创建工单、触发审批流程、执行变更、更新 CMDB，确保操作可追溯。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.operation-sim {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: rgba(0,0,0,0.4);
  padding: 20px;
}

.dialog {
  background: #fff;
  border-radius: 14px;
  width: 100%;
  max-width: 520px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}

.dialog-header h3 { font-size: 15px; font-weight: 700; color: #0f172a; margin: 0; }
.close-btn { font-size: 20px; color: #94a3b8; cursor: pointer; }

.dialog-body { 
  padding: 14px 20px; 
  overflow-y: auto;
  flex: 1;
}

.form-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.form-section:last-child { border-bottom: none; }

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 10px;
}

/* 当前配置 */
.current-config {
  background: #f8fafc;
  border-radius: 8px;
  padding: 12px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.config-item:last-child { border-bottom: none; }
.config-label { color: #64748b; }
.config-value { color: #0f172a; font-weight: 500; }
.mono { font-family: monospace; font-size: 11px; }

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
}

.status-dot.running { background: #16a34a; }

/* 规格选择 */
.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 8px;
}

.required { color: #ef4444; }

.spec-options {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.spec-card {
  padding: 10px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.spec-card.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.spec-card.current {
  border-color: #94a3b8;
  background: #f1f5f9;
  opacity: 0.7;
}

.spec-card:hover { border-color: #2563eb; }

.spec-name { font-size: 13px; font-weight: 700; color: #0f172a; }
.spec-spec { font-size: 11px; color: #64748b; margin: 2px 0; }
.spec-price { font-size: 11px; color: #2563eb; font-weight: 500; }

.spec-tag {
  position: absolute;
  top: -6px;
  right: -6px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 600;
}

.spec-tag.up { background: #fef3c7; color: #d97706; }
.spec-tag.down { background: #dbeafe; color: #2563eb; }
.spec-tag.current { background: #e2e8f0; color: #64748b; }

/* 变更影响 */
.impact-list { display: flex; flex-direction: column; gap: 8px; }

.impact-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
}

.impact-item.warning { background: #fef3c7; }
.impact-item.info { background: #eff6ff; }
.impact-item.success { background: #f0fdf4; }

.impact-icon { font-size: 16px; flex-shrink: 0; }
.impact-title { display: block; font-size: 12px; font-weight: 600; color: #0f172a; }
.impact-desc { display: block; font-size: 11px; color: #475569; margin-top: 2px; }

/* 联动说明 */
.capability-list { display: flex; flex-direction: column; gap: 6px; }

.capability-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: #f0fdf4;
  border-radius: 6px;
  font-size: 11px;
  color: #166534;
}

.cap-icon { font-size: 12px; }

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  flex-shrink: 0;
  background: #fff;
}

.btn-cancel {
  padding: 8px 16px;
  background: #f1f5f9;
  border-radius: 6px;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
}

.btn-submit {
  padding: 8px 16px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  border-radius: 6px;
  font-size: 12px;
  color: #fff;
  cursor: pointer;
}

.form-note {
  padding: 10px 20px;
  background: #f8fafc;
  font-size: 11px;
  color: #64748b;
  border-top: 1px solid #e5e7eb;
}
</style>
