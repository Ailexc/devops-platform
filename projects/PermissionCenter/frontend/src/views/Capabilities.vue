<template>
  <div class="caps-page">
    <PageHeader title="能力管理" desc="能力是应用对外暴露权限的统一载体：查看 / 编辑 / 授权管理 / 上架下架">
      <template #actions>
        <select v-model="filterApp" class="filter-select" @change="applyFilter">
          <option value="">全部应用</option>
          <option v-for="a in allApps" :key="a.id" :value="a.code">{{ a.name }}（{{ a.code }}）</option>
        </select>
        <select v-model="filterStatus" class="filter-select" @change="applyFilter">
          <option value="">全部状态</option>
          <option value="published">已发布</option>
          <option value="draft">草稿</option>
        </select>
      </template>
    </PageHeader>

    <div v-if="!isOwner && !isAdmin" class="notice">🔒 你暂时没有能力管理权限（仅应用 owner 可管理自己应用下的能力；管理员可见全部）。</div>

    <div v-if="me" class="new-cap-bar">
      <button class="btn btn-primary" @click="showCreate = true">＋ 新增能力</button>
    </div>

    <!-- 新增能力弹窗 -->
    <div v-if="showCreate" class="modal-mask" @click.self="showCreate = false">
      <div class="modal-box">
        <div class="modal-title">新增能力</div>
        <label>所属应用
          <select v-model="newCap.appId" class="input">
            <option v-for="a in allApps" :key="a.id" :value="a.id">{{ a.name }}（{{ a.code }}）</option>
          </select>
        </label>
        <label>能力名称
          <input v-model="newCap.name" class="input" placeholder="如：网络管理、磁盘管理" />
        </label>
        <label>能力描述
          <textarea v-model="newCap.description" class="input" rows="2" placeholder="一句话描述该能力…" />
        </label>
        <label>可见性
          <select v-model="newCap.visibility" class="input">
            <option value="public">全员可见</option>
            <option value="org_visible">仅指定组织可见</option>
            <option value="hidden">隐身</option>
          </select>
        </label>
        <div class="modal-foot">
          <button class="btn btn-ghost" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="doCreate" :disabled="creating">{{ creating ? '创建中…' : '创建' }}</button>
        </div>
        <div v-if="createErr" class="modal-err">{{ createErr }}</div>
      </div>
    </div>

    <div class="cap-grid">
      <div v-for="c in filtered" :key="c.id" class="cap-card">
        <div class="cap-top">
          <div class="cap-icon" :class="toneOf(c)">{{ iconOf(c) }}</div>
          <div style="flex:1;min-width:0;">
            <div class="cap-name">{{ c.name }}</div>
            <div class="cap-app">{{ appName(c.app_id) }} <span class="mono">· {{ appCode(c.app_id) }}</span></div>
          </div>
          <span class="tag" :class="c.status === 'published' ? 'tag-ok' : 'tag-warn'">{{ c.status === 'published' ? '已发布' : '草稿' }}</span>
        </div>
        <div class="cap-desc">{{ c.description || '—' }}</div>
        <div class="cap-tags">
          <span class="tag" :class="c.visibility === 'hidden' ? 'tag-red' : c.visibility === 'org_visible' ? 'tag-amber' : 'tag-blue'">{{ visLabel(c) }}</span>
          <span class="tag tag-gray">{{ c.presets?.length || 0 }} 预设</span>
          <span class="tag" :class="hasDataControl(c) ? 'tag-ok' : 'tag-gray'">{{ hasDataControl(c) ? '数据级' : '接口级' }}</span>
          <span class="tag tag-gray">v{{ c.version }}</span>
        </div>
        <div class="cap-foot">
          <router-link :to="`/apps/${c.app_id}/capabilities/${c.id}?view=1`" class="btn btn-sm">👁️ 查看</router-link>
          <router-link :to="`/apps/${c.app_id}/capabilities/${c.id}`" class="btn btn-sm">✏️ 编辑</router-link>
          <router-link :to="`/apps/${c.app_id}/capabilities/${c.id}/authz`" class="btn btn-sm">🔑 授权管理</router-link>
        </div>
      </div>
    </div>
    <EmptyState v-if="!filtered.length" text="暂无能力（可在应用详情触发「推断能力」生成）" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import PageHeader from '../components/PageHeader.vue'
import EmptyState from '../components/EmptyState.vue'

const route = useRoute()
const allApps = ref<any[]>([])
const caps = ref<any[]>([])
const me = ref<any>(null)
const filterApp = ref((route.query.app as string) || '')
const filterStatus = ref('')
const showCreate = ref(false)
const creating = ref(false)
const createErr = ref('')
const newCap = reactive({
  appId: 0,
  name: '',
  description: '',
  visibility: 'public',
})

const isAdmin = computed(() => me.value?.user?.username === 'admin')
const ownedAppIDs = computed(() => new Set((me.value?.apps || []).map((a: any) => a.id)))
const isOwner = computed(() => ownedAppIDs.value.size > 0)

const filtered = computed(() => {
  return caps.value.filter((c: any) => {
    if (!isAdmin.value && !ownedAppIDs.value.has(c.app_id)) return false
    if (filterApp.value && appCode(c.app_id) !== filterApp.value) return false
    if (filterStatus.value && c.status !== filterStatus.value) return false
    return true
  })
})

function appName(id: number) { return allApps.value.find(a => a.id === id)?.name || `#${id}` }
function appCode(id: number) { return allApps.value.find(a => a.id === id)?.code || `#${id}` }
function iconOf(c: any) { return c.name.includes('主机') ? '🖥️' : c.name.includes('数据库') ? '🗄️' : c.name.includes('资源') ? '☁️' : '📦' }
function toneOf(c: any) { return c.name.includes('主机') ? 'blue' : c.name.includes('数据库') ? 'amber' : 'cyan' }
function visLabel(c: any) {
  return c.visibility === 'hidden' ? '隐身' : c.visibility === 'org_visible' ? '组织可见' : '全员可见'
}
function hasDataControl(c: any) { return (c.presets || []).some((p: any) => p.data_control) }
function applyFilter() { /* computed reacts */ }

async function doCreate() {
  if (!newCap.appId || !newCap.name.trim()) {
    createErr.value = '请填写应用和能力名称'
    return
  }
  creating.value = true
  createErr.value = ''
  try {
    const created = await api.createCapability(newCap.appId, {
      name: newCap.name.trim(),
      description: newCap.description.trim(),
      visibility: newCap.visibility,
      grantee_types: ['user', 'org', 'group', 'app'],
      enforcement_mode: 'gateway',
    })
    showCreate.value = false
    newCap.name = ''
    newCap.description = ''
    newCap.visibility = 'public'
    // 跳转到编辑页
    window.location.href = `/apps/${newCap.appId}/capabilities/${created.id}`
  } catch (e: any) {
    createErr.value = '创建失败：' + e.message
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  try {
    const [appsData, meData] = await Promise.all([api.apps(), api.me()])
    allApps.value = (appsData as any).items || []
    me.value = meData
    // 默认选中第一个应用
    if (allApps.value.length && !newCap.appId) {
      newCap.appId = allApps.value[0].id
    }
    const list: any[] = []
    for (const a of allApps.value) {
      try {
        const r: any = await api.capabilities(a.id)
        list.push(...(r.items || []).map((c: any) => ({ ...c, app_id: a.id })))
      } catch { /* skip */ }
    }
    caps.value = list
  } catch (e: any) { console.error(e) }
})
</script>

<style scoped>
.caps-page { }
.notice { padding: 12px 16px; border-radius: var(--radius); background: var(--warning-bg); border: 1px solid rgba(217,119,6,.3); color: var(--warning); font-size: 13px; margin-bottom: 16px; }
.filter-select { height: 34px; padding: 0 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.cap-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow-sm); transition: box-shadow .2s, border-color .2s, transform .2s; }
.cap-card:hover { border-color: var(--border-strong); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.cap-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.cap-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }
.cap-icon.blue { background: var(--brand-soft); }
.cap-icon.amber { background: var(--warning-bg); }
.cap-icon.cyan { background: var(--info-bg); }
.cap-name { font-size: 15px; font-weight: 600; }
.cap-app { font-size: 12px; color: var(--text-tertiary); }
.cap-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
.cap-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.cap-foot { display: flex; gap: 8px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-warn { background: var(--warning-bg); color: var(--warning); }
.tag-red { background: var(--danger-bg); color: var(--danger); }
.tag-amber { background: var(--warning-bg); color: var(--warning); }
.tag-blue { background: var(--brand-soft); color: var(--brand-strong); }
.tag-gray { background: var(--bg-inset); color: var(--text-tertiary); border: 1px solid var(--border); }
.btn { display: inline-flex; align-items: center; gap: 5px; height: 30px; padding: 0 12px; border-radius: 8px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); color: var(--text); cursor: pointer; text-decoration: none; }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-sm { font-size: 12px; }
.btn-primary { background: var(--brand); color: #fff; border-color: var(--brand); }
.btn-primary:hover { background: var(--brand-strong); }
.btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.btn-ghost { background: transparent; border-color: transparent; }
.btn-ghost:hover { background: var(--bg-hover); }
.new-cap-bar { margin-bottom: 16px; }
.input { width: 100%; padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text); font-size: 13px; }
.input:focus { outline: none; border-color: var(--brand); }
.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,.35); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; width: 440px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,.2); display: flex; flex-direction: column; gap: 14px; }
.modal-title { font-size: 16px; font-weight: 700; }
.modal-box label { font-size: 13px; font-weight: 600; display: flex; flex-direction: column; gap: 5px; }
.modal-foot { display: flex; gap: 8px; justify-content: flex-end; margin-top: 4px; }
.modal-err { font-size: 12px; color: var(--danger); }
</style>
