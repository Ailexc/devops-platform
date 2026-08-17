<template>
  <div class="my-groups-page">
    <header class="page-header">
      <h1>我的自建组 / 身份</h1>
      <span class="page-desc">我在组织与自建组中的身份、管理范围一览</span>
    </header>

    <!-- 我的身份（FR-2.4） -->
    <div v-if="overview" class="panel identity-panel">
      <div class="identity-row">
        <span class="identity-label">组织身份</span>
        <div class="org-identity-list">
          <template v-if="identity.orgs?.length">
            <div v-for="g in identity.orgs" :key="g.id" class="org-identity-row">
              <span class="org-path mono">{{ (g.path_names || [g.name]).join(' → ') }}</span>
              <span class="tag" :class="g.my_role === 2 ? 'tag-admin' : ''">{{ g.my_role === 2 ? '组长' : '成员' }}</span>
            </div>
          </template>
          <span v-else class="text-secondary">无</span>
        </div>
      </div>
      <div class="identity-row">
        <span class="identity-label">自建组身份</span>
        <span class="text-secondary">
          <template v-if="customGroups.length">{{ customGroups.map((g: any) => `${g.name}（${g.my_role === 2 ? '组长' : '成员'}）`).join('、') }}</template>
          <template v-else>无</template>
        </span>
      </div>
      <div class="identity-row">
        <span class="identity-label">应用身份</span>
        <span class="text-secondary">
          <template v-if="identity.owned_apps?.length">{{ identity.owned_apps.map((a: any) => a.name).join('、') }}（owner）</template>
          <template v-else>无</template>
        </span>
      </div>
      <div class="identity-row">
        <span class="identity-label">审批人</span>
        <span class="text-secondary">{{ identity.approver ? '是（应用 owner / 组 admin）' : '否' }}</span>
      </div>
    </div>

    <!-- 我的自建组（FR-2.3） -->
    <div class="section-title">我的自建组</div>
    <div class="panel">
      <div v-if="customGroups.length === 0" class="empty-state">暂未加入任何自建组</div>
      <div v-for="g in customGroups" :key="g.id" class="group-card clickable" @click="$router.push(`/groups/${g.id}`)">
        <div class="group-card-header">
          <div>
            <span class="group-name">{{ g.name }}</span>
            <span class="tag" :class="g.my_role === 2 ? 'tag-admin' : ''">{{ g.my_role === 2 ? '组长' : '成员' }}</span>
          </div>
          <span class="text-secondary" style="font-size: 12px;">成员 {{ g.members?.length || 0 }} 人</span>
        </div>
        <div class="group-card-body">
          <div class="text-secondary" style="font-size: 12px; margin-bottom: 8px;">
            能力包 {{ groupCaps(g.id).length }} 个 · 接口权限 {{ g.permissions?.length || 0 }} 项
            <template v-if="g.expires_at"> · 有效期至 {{ fmtDate(g.expires_at) }}</template>
          </div>
          <div v-if="groupCaps(g.id).length" class="action-list" style="margin-bottom: 8px;">
            <router-link v-for="c in groupCaps(g.id)" :key="c.request_id" :to="`/requests/${c.request_id}`" class="cap-chip">
              {{ c.capability_name }} <span class="mono">/ {{ c.preset_name }}</span>
              <span class="cap-req">#{{ c.request_id }}</span>
            </router-link>
          </div>
          <div v-if="g.permissions?.length" class="action-list">
            <span v-for="a in g.permissions.slice(0, 8)" :key="a.id" class="action-tag">{{ a.code }}</span>
            <span v-if="g.permissions.length > 8" class="action-tag">+{{ g.permissions.length - 8 }}</span>
          </div>
          <div class="member-list">
            <span v-for="m in g.members || []" :key="m.id" class="member-chip" :title="m.dept ? `${m.display_name || m.username} · ${m.dept}` : m.display_name || m.username">{{ m.display_name || m.username }}<span v-if="m.dept" class="member-dept">{{ m.dept }}</span></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '../api/client'

const overview = ref<any>(null)
const customGroups = ref<any[]>([])
const capPerms = ref<any>({ group: [] })

const identity = computed(() => overview.value?.identity || {})

onMounted(async () => {
  try {
    const [ov, groups, caps] = await Promise.all([api.meOverview(), api.meGroups(), api.meCapabilityPermissions()])
    overview.value = ov
    customGroups.value = (groups as any).items || []
    capPerms.value = caps
  } catch { /* partial */ }
})

function groupCaps(groupId: number) {
  return (capPerms.value.group || []).filter((c: any) => c.grantee_id === groupId)
}

function fmtDate(v: any): string {
  if (!v) return ''
  return new Date(v).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.my-groups-page { max-width: 1200px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); }

.panel { border: 1px solid var(--border); background: var(--bg); }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }

.identity-panel { display: flex; flex-direction: column; }
.identity-row { display: flex; gap: 16px; padding: 12px 16px; border-bottom: 1px solid var(--border); font-size: 13px; }
.identity-row:last-child { border-bottom: none; }
.identity-label { min-width: 90px; color: var(--text-secondary); font-size: 12px; }
.org-identity-list { display: flex; flex-direction: column; gap: 6px; }
.org-identity-row { display: flex; align-items: center; gap: 10px; }
.org-path { font-family: var(--font-mono); font-size: 12px; }

.group-card { border-bottom: 1px solid var(--border); }
.group-card:last-child { border-bottom: none; }
.group-card.clickable { cursor: pointer; }
.group-card.clickable:hover { background: var(--bg-hover); }
.group-card-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; background: var(--bg-secondary); }
.group-name { font-size: 14px; font-weight: 600; margin-right: 10px; }
.group-card-body { padding: 12px 16px; }

.action-list { display: flex; flex-wrap: wrap; gap: 6px; }
.cap-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border: 1px solid var(--border); border-radius: 999px; font-size: 12px; text-decoration: none; color: var(--text); background: var(--bg-card); }
.cap-chip:hover { border-color: var(--brand); color: var(--brand-strong); }
.cap-req { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); }
.action-tag { font-family: var(--font-mono); font-size: 11px; padding: 3px 8px; background: var(--bg-tertiary); border: 1px solid var(--border); }
.member-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.member-chip { font-size: 12px; padding: 2px 10px; border: 1px solid var(--border); border-radius: 999px; display: inline-flex; align-items: center; gap: 4px; }
.member-dept { font-size: 10px; color: var(--text-tertiary); font-family: var(--font-mono); }

.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; background: var(--bg-tertiary); text-transform: uppercase; letter-spacing: 0.5px; }
.tag-admin { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.text-secondary { color: var(--text-secondary); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
