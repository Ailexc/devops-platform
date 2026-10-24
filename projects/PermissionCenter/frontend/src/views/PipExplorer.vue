<template>
  <div class="pip-page">
    <header class="page-header">
      <h1>身份解析（PIP）</h1>
      <span class="page-desc">主体 → 组织/组 → 祖先链 → 组权限 → 个人策略 → OpenFGA 数据级关系</span>
    </header>

    <div class="search-bar">
      <input v-model="user" class="search-input" placeholder="输入用户名（alice / bob / admin / client:cloud-mgmt）" @keyup.enter="load" />
      <button class="btn btn-primary" @click="load">解析</button>
      <div class="quick">
        <a v-for="u in ['alice', 'bob', 'admin', 'client:cloud-mgmt']" :key="u" @click="quick(u)">{{ u }}</a>
      </div>
    </div>

    <div v-if="data" class="grid">
      <!-- 主体信息 -->
      <div class="panel">
        <div class="panel-title">主体</div>
        <div class="card-body">
          <div class="kv"><span class="k">主体</span><span class="mono">{{ data.subject }}</span></div>
          <div class="kv"><span class="k">类型</span><span>{{ data.subject_type === 'user' ? '用户' : '程序身份（M2M）' }}</span></div>
          <div class="kv"><span class="k">PDP Key</span><span class="mono">{{ data.subject_key }}</span></div>
          <div v-if="data.user" class="kv"><span class="k">显示名</span><span>{{ data.user.display_name }}</span></div>
          <div v-if="data.user" class="kv"><span class="k">属性</span><span class="mono">{{ JSON.stringify(data.user.attributes || {}) }}</span></div>
        </div>
      </div>

      <!-- 直接隶属组 -->
      <div class="panel">
        <div class="panel-title">直接隶属（{{ (data.direct_groups || []).length }}）</div>
        <div class="card-body">
          <div v-for="g in data.direct_groups || []" :key="g.id" class="group-chip">
            <span>{{ g.name }}</span>
            <span class="tag" :class="g.type === 1 ? 'tag-org' : 'tag-custom'">{{ g.type === 1 ? '组织' : '自建组' }}</span>
            <span class="tag" :class="g.role === 2 ? 'tag-admin' : ''">{{ g.role_name }}</span>
            <span class="mono text-secondary" style="font-size: 10px;">{{ g.path }}</span>
          </div>
          <div v-if="!(data.direct_groups || []).length" class="empty-state" style="padding: 12px;">无直接隶属组</div>
        </div>
      </div>

      <!-- 祖先链 -->
      <div class="panel">
        <div class="panel-title">组层级祖先链（{{ (data.ancestor_chain || []).length }}）</div>
        <div class="card-body">
          <div class="chain">
            <template v-for="(g, i) in data.ancestor_chain || []" :key="g.id">
              <span class="chain-node mono">{{ g.name }}</span>
              <span v-if="i < (data.ancestor_chain || []).length - 1" class="chain-arrow">→</span>
            </template>
          </div>
          <div v-if="!(data.ancestor_chain || []).length" class="empty-state" style="padding: 12px;">无祖先链</div>
        </div>
      </div>

      <!-- 组权限 -->
      <div class="panel">
        <div class="panel-title">组权限点（{{ (data.group_actions || []).length }} 组）</div>
        <div class="card-body">
          <div v-for="ga in data.group_actions || []" :key="ga.group_id" class="group-perm">
            <div class="gp-name">{{ ga.group_name }}</div>
            <div class="action-list">
              <span v-for="a in ga.actions" :key="a.id" class="action-tag">{{ a.code }}</span>
            </div>
          </div>
          <div v-if="!(data.group_actions || []).length" class="empty-state" style="padding: 12px;">无组权限</div>
        </div>
      </div>

      <!-- 个人策略 -->
      <div class="panel">
        <div class="panel-title">个人策略（{{ (data.personal_policies || []).length }}）</div>
        <div class="card-body">
          <div v-for="p in data.personal_policies || []" :key="p.id" class="policy-chip">
            <span class="mono">{{ p.name }}</span>
            <span class="tag" :class="p.effect === 1 ? 'tag-success' : 'tag-danger'">{{ p.effect === 1 ? 'allow' : 'deny' }}</span>
            <span class="mono text-secondary" style="font-size: 10px;">{{ (p.actions || []).map((a: any) => a.code).join('、') }}</span>
            <span v-if="p.expires_at" class="mono text-secondary" style="font-size: 10px;">至 {{ fmtDate(p.expires_at) }}</span>
          </div>
          <div v-if="!(data.personal_policies || []).length" class="empty-state" style="padding: 12px;">无个人策略</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api/client'

const user = ref('alice')
const data = ref<any>(null)

async function load() {
  if (!user.value) return
  try {
    data.value = await api.debugPip(user.value.trim())
  } catch (e: any) {
    data.value = { error: e.message }
  }
}
function quick(u: string) {
  user.value = u
  load()
}
function fmtDate(v: any): string {
  return v ? new Date(v).toLocaleDateString('zh-CN') : ''
}
onMounted(load)
</script>

<style scoped>
.pip-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.search-bar { display: flex; gap: 8px; align-items: center; margin-bottom: 16px; }
.search-input { flex: 1; padding: 8px 12px; font-size: 13px; font-family: var(--font-mono); border: 1px solid var(--border); background: var(--bg); color: var(--text); outline: none; }
.search-input:focus { border-color: var(--accent); }
.quick { display: flex; gap: 8px; }
.quick a { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); cursor: pointer; }
.quick a:hover { color: var(--accent-text); }

.grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1px; background: var(--border); border: 1px solid var(--border); }
.panel { background: var(--bg); }
.panel-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); padding: 10px 16px; border-bottom: 1px solid var(--border); font-family: var(--font-mono); }
.card-body { padding: 12px 16px; display: flex; flex-direction: column; gap: 8px; }

.kv { display: flex; gap: 12px; font-size: 13px; }
.kv .k { min-width: 70px; color: var(--text-secondary); font-size: 12px; }

.group-chip { display: flex; align-items: center; gap: 8px; font-size: 13px; padding: 4px 0; border-bottom: 1px dashed var(--border); }
.group-chip:last-child { border-bottom: none; }

.chain { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: 12px; }
.chain-node { padding: 3px 10px; background: var(--bg-tertiary); border: 1px solid var(--border); }
.chain-arrow { color: var(--text-tertiary); }

.group-perm { margin-bottom: 8px; }
.gp-name { font-size: 12px; font-weight: 600; margin-bottom: 4px; }
.action-list { display: flex; flex-wrap: wrap; gap: 4px; }
.action-tag { font-family: var(--font-mono); font-size: 10px; padding: 2px 6px; background: var(--bg-tertiary); border: 1px solid var(--border); }

.policy-chip { display: flex; align-items: center; gap: 8px; font-size: 12px; padding: 4px 0; border-bottom: 1px dashed var(--border); }
.policy-chip:last-child { border-bottom: none; }

.ofga-row { display: flex; align-items: center; gap: 6px; font-size: 12px; padding: 4px 0; border-bottom: 1px dashed var(--border); }
.ofga-row:last-child { border-bottom: none; }
.ofga-rel { color: var(--text-tertiary); font-family: var(--font-mono); font-size: 11px; }

.btn { padding: 8px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; font-family: var(--font-mono); white-space: nowrap; }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-org { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.tag-custom { background: rgba(168, 85, 247, 0.15); color: #a855f7; }
.tag-admin { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-success { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.tag-danger { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.empty-state { padding: 12px; text-align: center; color: var(--text-tertiary); font-size: 12px; }
</style>
