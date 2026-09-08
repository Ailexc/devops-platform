<template>
  <div class="mock-screen preset-select-screen">
    <div class="mock-topbar">
      <div class="mock-breadcrumb">能力市场 / 主机监控 / <b>选择预设</b></div>
      <div class="mock-user">👤 小红</div>
    </div>
    <div class="mock-content">
      <h2 class="mock-title">🔖 选择权限预设</h2>

      <div class="preset-list">
        <div class="preset-card" v-for="p in presets" :key="p.name" :class="{ selected: p.selected }">
          <div class="preset-header">
            <div class="preset-name">{{ p.name }}</div>
            <div class="preset-badge" v-if="p.selected">✅ 已选</div>
          </div>
          <div class="preset-desc">{{ p.desc }}</div>
          <div class="preset-apis">
            <div class="preset-apis-title">接口明细（程序对接契约）—— 点击接口可查看调用契约</div>
            <template v-for="op in p.ops" :key="op.action">
              <div class="op-row" @click="toggleOp(p.name, op.action)">
                <span class="op-method" :class="op.method.toLowerCase()">{{ op.method }}</span>
                <span class="op-path mono">{{ op.path }}</span>
                <span class="op-action mono">{{ op.action }}</span>
                <span class="op-chev">{{ expanded === p.name + ':' + op.action ? '▾' : '▸' }}</span>
              </div>
              <div v-if="expanded === p.name + ':' + op.action" class="op-ex">
                <div class="ex"><div class="ex-t">⬆️ 请求示例</div><pre class="ex-c">{{ op.req }}</pre></div>
                <div class="ex"><div class="ex-t">⬇️ 响应示例</div><pre class="ex-c">{{ op.resp }}</pre></div>
              </div>
            </template>
          </div>
          <div class="preset-meta">
            <span>👤 组织/人员可申请</span>
            <span>🔐 含数据级控制</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const presets = [
  {
    name: '只读监控',
    desc: '仅查看主机列表与详情，适用于日常巡检和监控场景',
    selected: true,
    ops: [
      { method: 'GET', path: '/api/v1/hosts', action: 'host:list', req: 'GET /api/v1/hosts?page=1&page_size=20', resp: '{ "items": [{ "id": 1, "name": "web-01", "env": "prod" }], "total": 2 }' },
      { method: 'GET', path: '/api/v1/hosts/{id}', action: 'host:read', req: 'GET /api/v1/hosts/1', resp: '{ "id": 1, "name": "web-01", "env": "prod", "ip": "10.0.0.11" }' },
    ],
  },
  {
    name: '完整监控',
    desc: '查看 + 创建 + 编辑主机，适用于运维操作场景',
    selected: false,
    ops: [
      { method: 'GET', path: '/api/v1/hosts', action: 'host:list', req: 'GET /api/v1/hosts?page=1&page_size=20', resp: '{ "items": [], "total": 2 }' },
      { method: 'GET', path: '/api/v1/hosts/{id}', action: 'host:read', req: 'GET /api/v1/hosts/1', resp: '{ "id": 1, "name": "web-01" }' },
      { method: 'POST', path: '/api/v1/hosts', action: 'host:create', req: 'POST /api/v1/hosts\n{ "name": "web-02", "env": "prod", "region": "cn-east-1" }', resp: '201 Created\n{ "id": 2, "name": "web-02" }' },
      { method: 'PUT', path: '/api/v1/hosts/{id}', action: 'host:update', req: 'PUT /api/v1/hosts/2\n{ "env": "staging" }', resp: '200 OK\n{ "id": 2, "env": "staging" }' },
    ],
  },
]

const expanded = ref('')
function toggleOp(preset: string, action: string) {
  const key = preset + ':' + action
  expanded.value = expanded.value === key ? '' : key
}
</script>

<style scoped>
.mock-screen { width: 100%; flex: 1; min-height: 0; display: flex; flex-direction: column; background: var(--bg); }
.mock-topbar { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: var(--bg-card); border-bottom: 1px solid var(--border); font-size: 13px; color: var(--text-secondary); }
.mock-user { font-weight: 500; }
.mock-content { flex: 1; padding: 24px; overflow: auto; }
.mock-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 20px; }
.preset-list { display: flex; flex-direction: column; gap: 14px; }
.preset-card { background: var(--bg-card); border: 1.5px solid var(--border); border-radius: 10px; padding: 18px; cursor: pointer; transition: all 0.15s; }
.preset-card.selected { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-soft); background: var(--brand-softer); }
.preset-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.preset-name { font-size: 15px; font-weight: 600; color: var(--text); }
.preset-badge { font-size: 12px; color: var(--success); font-weight: 600; }
.preset-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.preset-apis { margin-bottom: 12px; }
.preset-apis-title { font-size: 11px; color: var(--text-tertiary); margin-bottom: 6px; }
.op-row { display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: var(--bg-secondary); border-radius: 6px; margin-bottom: 4px; cursor: pointer; transition: background 0.15s; }
.op-row:hover { background: var(--brand-softer); }
.op-method { font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px; color: #fff; flex-shrink: 0; }
.op-method.get { background: var(--success); }
.op-method.post { background: var(--warning); }
.op-method.put { background: var(--brand); }
.op-method.del { background: var(--danger); }
.op-path { font-size: 11px; color: var(--text); flex: 1; }
.op-action { font-size: 10px; color: var(--text-tertiary); }
.op-chev { font-size: 11px; color: var(--text-tertiary); }
.op-ex { background: #1e293b; border-radius: 6px; padding: 8px 10px; margin: 4px 0 8px; }
.ex { margin-bottom: 6px; }
.ex:last-child { margin-bottom: 0; }
.ex-t { font-size: 10px; color: #94a3b8; margin-bottom: 3px; }
.ex-c { margin: 0; font-family: var(--font-mono); font-size: 11px; color: #e2e8f0; white-space: pre-wrap; word-break: break-all; line-height: 1.5; }
.preset-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-tertiary); }
</style>
