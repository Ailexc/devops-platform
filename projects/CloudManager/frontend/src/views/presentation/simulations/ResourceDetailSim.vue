<script setup lang="ts">
import { ref } from 'vue'

const activeTab = ref('info')

const tabs = [
  { id: 'info', label: '基础信息', icon: '📋' },
  { id: 'network', label: '网络与安全', icon: '🌐' },
  { id: 'storage', label: '存储', icon: '💿' },
  { id: 'tags', label: '标签', icon: '🏷️' },
  { id: 'monitoring', label: '监控', icon: '📊' },
  { id: 'events', label: '事件', icon: '📜' },
]
</script>

<template>
  <div class="detail-sim">
    <div class="breadcrumb">
      <span class="link">☁️ AWS</span> / <span class="link">🖥️ 计算资源</span> / <span>云主机</span> / <span>web-server-01</span>
    </div>

    <div class="title-bar">
      <div class="title-left">
        <h2>🖥️ web-server-01</h2>
        <div class="badges">
          <span class="status running">✅ 运行中</span>
          <span class="badge instance">EC2 实例</span>
          <span class="badge region">us-east-1</span>
        </div>
      </div>
      <div class="title-actions">
        <button class="action-btn stop">⏹ 停止</button>
        <button class="action-btn reboot">🔄 重启</button>
        <button class="action-btn settings">⚙️ 变更</button>
      </div>
    </div>

    <!-- Tab 页 -->
    <div class="tabs-bar">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        class="tab-item"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- Tab 内容 -->
    <div class="tab-content">
      <!-- 基础信息 -->
      <div v-if="activeTab === 'info'" class="info-grid">
        <div class="info-section">
          <h4>实例信息</h4>
          <div class="info-list">
            <div class="info-item"><span class="label">实例 ID</span><span class="value mono">i-0a1b2c3d4e5f6g7h8</span></div>
            <div class="info-item"><span class="label">实例状态</span><span class="value"><span class="status-dot running"></span> 运行中</span></div>
            <div class="info-item"><span class="label">实例类型</span><span class="value">m5.xlarge</span></div>
            <div class="info-item"><span class="label">vCPU</span><span class="value">4 核</span></div>
            <div class="info-item"><span class="label">内存</span><span class="value">16 GB</span></div>
            <div class="info-item"><span class="label">AMI</span><span class="value mono">ami-0abcdef1234567890</span></div>
            <div class="info-item"><span class="label">平台</span><span class="value">Linux/Unix</span></div>
          </div>
        </div>
        <div class="info-section">
          <h4>网络与位置</h4>
          <div class="info-list">
            <div class="info-item"><span class="label">VPC</span><span class="value">vpc-0a1b2c3d (prod-vpc)</span></div>
            <div class="info-item"><span class="label">子网</span><span class="value">subnet-1a2b3c4d (pub-subnet-1a)</span></div>
            <div class="info-item"><span class="label">安全组</span><span class="value">sg-5e6f7g8h (web-sg)</span></div>
            <div class="info-item"><span class="label">私有 IP</span><span class="value mono">10.0.1.100</span></div>
            <div class="info-item"><span class="label">公有 IP</span><span class="value mono">52.23.xx.xx</span></div>
            <div class="info-item"><span class="label">可用区</span><span class="value">us-east-1a</span></div>
          </div>
        </div>
        <div class="info-section">
          <h4>时间与监控</h4>
          <div class="info-list">
            <div class="info-item"><span class="label">启动时间</span><span class="value">2026-07-15 10:30:00</span></div>
            <div class="info-item"><span class="label">启动方式</span><span class="value">按需实例</span></div>
            <div class="info-item"><span class="label">IAM 角色</span><span class="value">ec2-web-server-role</span></div>
            <div class="info-item"><span class="label">监控</span><span class="value">✅ 已启用详细监控</span></div>
            <div class="info-item"><span class="label">自动恢复</span><span class="value">✅ 已启用</span></div>
          </div>
        </div>
      </div>

      <!-- 网络与安全 -->
      <div v-if="activeTab === 'network'" class="network-tab">
        <div class="info-section">
          <h4>🛡️ 安全组规则</h4>
          <table class="mini-table">
            <thead>
              <tr><th>类型</th><th>协议</th><th>端口</th><th>来源</th><th>说明</th></tr>
            </thead>
            <tbody>
              <tr><td>入站</td><td>TCP</td><td>80</td><td>0.0.0.0/0</td><td>HTTP</td></tr>
              <tr><td>入站</td><td>TCP</td><td>443</td><td>0.0.0.0/0</td><td>HTTPS</td></tr>
              <tr><td>入站</td><td>TCP</td><td>22</td><td>10.0.0.0/16</td><td>SSH (内网)</td></tr>
              <tr><td>出站</td><td>全部</td><td>全部</td><td>0.0.0.0/0</td><td>允许全部出站</td></tr>
            </tbody>
          </table>
        </div>
        <div class="info-section">
          <h4>🔗 ENI 网络接口</h4>
          <div class="info-list">
            <div class="info-item"><span class="label">ENI ID</span><span class="value mono">eni-0a1b2c3d4e5f</span></div>
            <div class="info-item"><span class="label">MAC 地址</span><span class="value mono">0a:1b:2c:3d:4e:5f</span></div>
            <div class="info-item"><span class="label">VPC</span><span class="value">prod-vpc</span></div>
            <div class="info-item"><span class="label">子网</span><span class="value">pub-subnet-1a</span></div>
          </div>
        </div>
      </div>

      <!-- 存储 -->
      <div v-if="activeTab === 'storage'" class="storage-tab">
        <div class="info-section">
          <h4>💿 块存储</h4>
          <table class="mini-table">
            <thead>
              <tr><th>设备名</th><th>卷 ID</th><th>类型</th><th>大小</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr><td>/dev/sda1</td><td class="mono">vol-0a1b2c3d</td><td>gp3</td><td>100 GB</td><td><span class="status-tag attached">已挂载</span></td></tr>
              <tr><td>/dev/sdf</td><td class="mono">vol-1b2c3d4e</td><td>gp3</td><td>500 GB</td><td><span class="status-tag attached">已挂载</span></td></tr>
            </tbody>
          </table>
        </div>
        <div class="info-section">
          <h4>📸 快照</h4>
          <div class="info-list">
            <div class="info-item"><span class="label">最新快照</span><span class="value">snap-20260801 (自动)</span></div>
            <div class="info-item"><span class="label">快照策略</span><span class="value">每日 02:00 UTC，保留7天</span></div>
          </div>
        </div>
      </div>

      <!-- 标签 -->
      <div v-if="activeTab === 'tags'" class="tags-tab">
        <div class="info-section">
          <h4>🏷️ 资源标签</h4>
          <div class="tags-grid">
            <div class="tag-item"><span class="tag-key">Name</span><span class="tag-value">web-server-01</span></div>
            <div class="tag-item"><span class="tag-key">Environment</span><span class="tag-value">production</span></div>
            <div class="tag-item"><span class="tag-key">Project</span><span class="tag-value">cloud-manager</span></div>
            <div class="tag-item"><span class="tag-key">Team</span><span class="tag-value">platform</span></div>
            <div class="tag-item"><span class="tag-key">CostCenter</span><span class="tag-value">CC-001</span></div>
            <div class="tag-item"><span class="tag-key">ManagedBy</span><span class="tag-value">cloud-manager</span></div>
          </div>
        </div>
      </div>

      <!-- 监控 -->
      <div v-if="activeTab === 'monitoring'" class="monitoring-tab">
        <div class="info-section">
          <h4>📊 CloudWatch 监控</h4>
          <div class="monitor-grid">
            <div class="monitor-card">
              <span class="monitor-label">CPU 使用率</span>
              <span class="monitor-value">23%</span>
              <div class="monitor-bar"><div class="bar-fill" style="width: 23%"></div></div>
            </div>
            <div class="monitor-card">
              <span class="monitor-label">内存使用率</span>
              <span class="monitor-value">67%</span>
              <div class="monitor-bar"><div class="bar-fill warn" style="width: 67%"></div></div>
            </div>
            <div class="monitor-card">
              <span class="monitor-label">磁盘使用率</span>
              <span class="monitor-value">45%</span>
              <div class="monitor-bar"><div class="bar-fill" style="width: 45%"></div></div>
            </div>
            <div class="monitor-card">
              <span class="monitor-label">网络入站</span>
              <span class="monitor-value">12.5 MB/s</span>
              <div class="monitor-bar"><div class="bar-fill" style="width: 35%"></div></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 事件 -->
      <div v-if="activeTab === 'events'" class="events-tab">
        <div class="info-section">
          <h4>📜 最近事件</h4>
          <div class="event-list">
            <div class="event-item">
              <span class="event-time">2026-08-08 14:30</span>
              <span class="event-type info">信息</span>
              <span class="event-desc">实例启动完成</span>
            </div>
            <div class="event-item">
              <span class="event-time">2026-08-01 10:15</span>
              <span class="event-type change">变更</span>
              <span class="event-desc">实例类型从 m5.large 变更为 m5.xlarge</span>
            </div>
            <div class="event-item">
              <span class="event-time">2026-07-20 09:00</span>
              <span class="event-type info">信息</span>
              <span class="event-desc">实例重启</span>
            </div>
            <div class="event-item">
              <span class="event-time">2026-07-15 10:30</span>
              <span class="event-type create">创建</span>
              <span class="event-desc">实例创建完成</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-sim {
  padding: 16px;
  background: #f1f5f9;
  height: 100%;
  overflow-y: auto;
}

.breadcrumb { font-size: 11px; color: #64748b; margin-bottom: 10px; }
.link { color: #2563eb; cursor: pointer; }

.title-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  background: #fff;
  padding: 16px;
  border-radius: 10px;
}

.title-left h2 { font-size: 18px; font-weight: 700; color: #0f172a; margin: 0 0 8px 0; }

.badges { display: flex; gap: 6px; }

.status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.status.running { background: #dcfce7; color: #16a34a; }

.badge {
  padding: 3px 10px;
  background: #f1f5f9;
  border-radius: 12px;
  font-size: 11px;
  color: #475569;
}

.title-actions { display: flex; gap: 6px; }

.action-btn {
  padding: 6px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 11px;
  background: #fff;
  color: #475569;
  cursor: pointer;
}

.action-btn.stop { color: #dc2626; border-color: #fca5a5; }
.action-btn.reboot { color: #d97706; border-color: #fcd34d; }

/* Tabs */
.tabs-bar {
  display: flex;
  gap: 2px;
  background: #fff;
  border-radius: 10px 10px 0 0;
  padding: 4px 4px 0;
  border-bottom: 1px solid #e2e8f0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 12px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-item:hover { color: #1e293b; }
.tab-item.active { color: #2563eb; border-bottom-color: #2563eb; font-weight: 500; }

.tab-icon { font-size: 14px; }

/* Tab Content */
.tab-content {
  background: #fff;
  border-radius: 0 0 10px 10px;
  padding: 16px;
}

.info-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.info-section:last-child { border-bottom: none; margin-bottom: 0; }

h4 {
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 10px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-list { display: flex; flex-direction: column; gap: 4px; }

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  border-bottom: 1px solid #f8fafc;
  font-size: 11px;
}

.info-item:last-child { border-bottom: none; }
.label { color: #64748b; }
.value { color: #0f172a; font-weight: 500; }
.mono { font-family: monospace; font-size: 10px; }

.status-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  margin-right: 4px;
}

.status-dot.running { background: #16a34a; }

/* Tables */
.mini-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.mini-table th {
  text-align: left;
  padding: 8px;
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  border-bottom: 1px solid #e2e8f0;
}

.mini-table td {
  padding: 8px;
  border-bottom: 1px solid #f1f5f9;
  color: #0f172a;
}

.status-tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.status-tag.attached { background: #dcfce7; color: #16a34a; }

/* Tags */
.tags-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.tag-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
}

.tag-key {
  width: 100px;
  font-size: 11px;
  font-weight: 600;
  color: #475569;
}

.tag-value {
  font-size: 11px;
  color: #0f172a;
}

/* Monitor */
.monitor-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.monitor-card {
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  text-align: center;
}

.monitor-label { display: block; font-size: 11px; color: #64748b; margin-bottom: 4px; }
.monitor-value { display: block; font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 8px; }

.monitor-bar {
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: #22c55e;
  border-radius: 2px;
}

.bar-fill.warn { background: #f59e0b; }

/* Events */
.event-list { display: flex; flex-direction: column; gap: 8px; }

.event-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 11px;
}

.event-time { width: 120px; color: #64748b; font-family: monospace; font-size: 10px; }

.event-type {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.event-type.info { background: #dbeafe; color: #2563eb; }
.event-type.change { background: #fef3c7; color: #d97706; }
.event-type.create { background: #dcfce7; color: #16a34a; }

.event-desc { color: #0f172a; }
</style>
