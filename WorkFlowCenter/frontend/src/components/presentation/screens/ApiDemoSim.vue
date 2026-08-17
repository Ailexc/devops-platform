<template>
  <div class="api-demo-sim">
    <div class="api-header">
      <span class="api-title">API 发起流程</span>
    </div>
    <div class="api-body">
      <div class="curl-card" :class="{ highlight: focus === 'curl' }">
        <div class="card-title">🚀 程序发起 — 申请服务器</div>
        <pre class="code-block"><span class="kw">curl</span> -X POST https://frontend.workflow.orb.local/api/v1/process-instances/start/ \
  -H <span class="str">"Content-Type: application/json"</span> \
  -H <span class="str">"X-App-Code: cmdb_sync"</span> \
  -H <span class="str">"X-App-Key: demo_cmdb_sync_key_2026"</span> \
  -d <span class="str">'{
    "definition_id": 1,
    "form_data": {
      "hostname": "web-prod-01",
      "cpu": 8,
      "memory": 16,
      "os": "CentOS 7",
      "reason": "线上扩容"
    }
  }'</span></pre>
      </div>

      <div class="response-card" :class="{ highlight: focus === 'response' }">
        <div class="card-title">📤 响应结果</div>
        <pre class="code-block response">{
  <span class="key">"id"</span>: 1,
  <span class="key">"instance_no"</span>: <span class="str">"SRV-2026-003"</span>,
  <span class="key">"status"</span>: <span class="str">"running"</span>,
  <span class="key">"current_node_key"</span>: <span class="str">"auto_create_host"</span>,
  <span class="key">"message"</span>: <span class="str">"流程已发起，正在自动执行"</span>
}</pre>
      </div>

      <div class="info-bar">
        <div class="info-item">
          <span class="info-icon">🔑</span>
          <span>API Key 认证</span>
        </div>
        <div class="info-item">
          <span class="info-icon">⚡</span>
          <span>跳过审批，直接执行</span>
        </div>
        <div class="info-item">
          <span class="info-icon">📋</span>
          <span>返回流程实例信息</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ focus?: string }>()
</script>

<style scoped lang="scss">
.api-demo-sim {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.api-header {
  height: 48px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.api-title { font-size: 14px; font-weight: 600; color: #1a1a2e; }

.api-body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.curl-card, .response-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  transition: all 0.3s;

  &.highlight {
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
  }
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 12px;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.6;
  margin: 0;
  font-family: 'SF Mono', 'JetBrains Mono', monospace;
  overflow-x: auto;

  &.response { background: #0d1117; }
}

.kw { color: #569cd6; }
.str { color: #ce9178; }
.key { color: #9cdcfe; }

.info-bar {
  display: flex;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 13px;
  color: #374151;
}

.info-icon { font-size: 16px; }
</style>
