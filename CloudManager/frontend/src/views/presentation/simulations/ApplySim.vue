<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<template>
  <div class="apply-sim">
    <div class="dialog-overlay">
      <div class="dialog">
        <div class="dialog-header">
          <h3>📋 申请云主机</h3>
          <span class="close-btn">×</span>
        </div>
        
        <div class="dialog-body">
          <div class="form-group" :class="{ highlighted: focus === 'spec' }">
            <label>规格选择</label>
            <div class="spec-options">
              <div class="spec-card selected">
                <div class="spec-name">4C8G</div>
                <div class="spec-price">¥0.52/小时</div>
                <div class="spec-desc">适合中小型应用</div>
              </div>
              <div class="spec-card">
                <div class="spec-name">8C16G</div>
                <div class="spec-price">¥1.04/小时</div>
                <div class="spec-desc">适合大型应用</div>
              </div>
              <div class="spec-card">
                <div class="spec-name">16C32G</div>
                <div class="spec-price">¥2.08/小时</div>
                <div class="spec-desc">适合高性能计算</div>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>云厂商</label>
              <div class="select-box">
                <span>AWS</span>
                <span class="arrow">▼</span>
              </div>
            </div>
            <div class="form-group">
              <label>地域</label>
              <div class="select-box">
                <span>us-east-1</span>
                <span class="arrow">▼</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>数量</label>
            <div class="quantity-box">
              <span class="qty-btn">-</span>
              <span class="qty-value">1</span>
              <span class="qty-btn">+</span>
            </div>
          </div>
        </div>

        <div class="dialog-footer" :class="{ highlighted: focus === 'submit' }">
          <span class="btn cancel">取消</span>
          <span class="btn submit">✅ 提交申请</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.apply-sim {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  padding: 20px;
}

.dialog {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 500px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

h3 {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0;
}

.close-btn {
  font-size: 24px;
  color: #94a3b8;
  cursor: pointer;
}

.dialog-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
  transition: all 0.3s;
}

.form-group.highlighted {
  outline: 2px solid #667eea;
  outline-offset: 4px;
  border-radius: 8px;
}

.form-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.spec-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.spec-card {
  padding: 12px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.spec-card.selected {
  border-color: #667eea;
  background: #eef2ff;
}

.spec-card:hover {
  border-color: #667eea;
}

.spec-name {
  font-size: 16px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.spec-price {
  font-size: 13px;
  color: #667eea;
  font-weight: 500;
  margin-bottom: 4px;
}

.spec-desc {
  font-size: 11px;
  color: #94a3b8;
}

.select-box {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  color: #1e293b;
}

.arrow { font-size: 10px; color: #94a3b8; }

.quantity-box {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.qty-btn {
  width: 28px;
  height: 28px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: #475569;
  cursor: pointer;
}

.qty-value {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a2e;
  min-width: 20px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.dialog-footer.highlighted {
  background: #f0fdf4;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
}

.btn.cancel {
  background: #f1f5f9;
  color: #64748b;
}

.btn.submit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}
</style>
