<script setup lang="ts">
</script>

<template>
  <div class="create-sim">
    <div class="dialog-overlay">
      <div class="dialog">
        <div class="dialog-header">
          <h3>🚀 申请云主机</h3>
          <span class="close-btn">×</span>
        </div>
        
        <div class="dialog-body">
          <!-- 基础配置 -->
          <div class="form-section">
            <div class="section-title">📋 基础配置</div>
            <div class="form-row">
              <div class="form-group">
                <label>主机名称 <span class="required">*</span></label>
                <input type="text" class="form-input" value="web-server-03" />
              </div>
              <div class="form-group">
                <label>数量</label>
                <input type="number" class="form-input" value="1" />
              </div>
            </div>
          </div>

          <!-- 规格选择 -->
          <div class="form-section">
            <div class="section-title">⚙️ 规格选择</div>
            <div class="spec-options">
              <div class="spec-card">
                <div class="spec-name">2C4G</div>
                <div class="spec-price">¥0.26/时</div>
                <div class="spec-desc">适合轻量应用</div>
              </div>
              <div class="spec-card selected">
                <div class="spec-name">4C8G</div>
                <div class="spec-price">¥0.52/时</div>
                <div class="spec-desc">适合中小型应用</div>
              </div>
              <div class="spec-card">
                <div class="spec-name">8C16G</div>
                <div class="spec-price">¥1.04/时</div>
                <div class="spec-desc">适合大型应用</div>
              </div>
            </div>
          </div>

          <!-- 网络配置 -->
          <div class="form-section">
            <div class="section-title">🌐 网络配置</div>
            <div class="form-row">
              <div class="form-group">
                <label>云厂商</label>
                <select class="form-select"><option>AWS</option></select>
              </div>
              <div class="form-group">
                <label>地域</label>
                <select class="form-select"><option>us-east-1 (弗吉尼亚)</option></select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>VPC</label>
                <select class="form-select"><option>prod-vpc (10.0.0.0/16)</option></select>
              </div>
              <div class="form-group">
                <label>子网</label>
                <select class="form-select"><option>pub-subnet-1 (10.0.1.0/24)</option></select>
              </div>
            </div>
            <div class="form-group">
              <label>安全组</label>
              <select class="form-select"><option>web-sg (HTTP/HTTPS/SSH)</option></select>
            </div>
          </div>

          <!-- 联动说明 -->
          <div class="form-section">
            <div class="section-title">🔗 联动能力</div>
            <div class="capability-list">
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">网络配置：自动创建/关联 VPC、子网、安全组</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">授权管理：自动配置 IAM 角色和策略</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">监控接入：自动关联 CloudWatch 监控</span>
              </div>
              <div class="capability-item">
                <span class="cap-icon">✅</span>
                <span class="cap-text">标签管理：自动打上项目/部门标签</span>
              </div>
            </div>
          </div>
        </div>

        <div class="dialog-footer">
          <span class="btn-cancel">取消</span>
          <span class="btn-submit">✅ 提交申请（将创建工单）</span>
        </div>

        <!-- 底部说明 -->
        <div class="form-note">
          💡 与直接在云控制台创建不同，这里的一次提交可以完成联动资源创建、网络配置、授权管理等多项能力，通过场景模板编排好，与工单系统联动。
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.create-sim {
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
  color: #1a1a2e;
  margin-bottom: 10px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 10px;
}

.form-group label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  margin-bottom: 4px;
}

.required { color: #ef4444; }

.form-input, .form-select {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 12px;
  background: #f8fafc;
}

.spec-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.spec-card {
  padding: 10px;
  background: #f8fafc;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.spec-card.selected {
  border-color: #667eea;
  background: #eef2ff;
}

.spec-card:hover { border-color: #667eea; }

.spec-name { font-size: 14px; font-weight: 700; color: #1a1a2e; }
.spec-price { font-size: 12px; color: #667eea; margin: 2px 0; }
.spec-desc { font-size: 10px; color: #94a3b8; }

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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
