<template>
  <div class="group-detail-page" v-if="group">
    <header class="page-header">
      <router-link :to="group?.type === 2 ? '/me/groups' : '/groups'" class="back-link">← {{ group?.type === 2 ? '我的自建组' : '组织与组' }}</router-link>
      <h1>{{ group.name }}</h1>
      <span class="page-desc">
        <span class="tag" :class="group.type === 1 ? 'tag-org' : 'tag-custom'">{{ group.type === 1 ? '组织' : '自建组' }}</span>
        <template v-if="group.type === 1">
          <span class="tag" :class="isLeaf ? 'tag-leaf' : 'tag-ro'">{{ isLeaf ? '可配置' : '只读' }}</span>
        </template>
        <span class="text-secondary" style="margin-left: 8px;">路径 {{ group.path }}</span>
      </span>
    </header>

    <div class="panel info-panel">
      <div class="info-row"><span class="info-label">有效期</span><span>{{ fmtDate(group.expires_at) || '永久' }}</span></div>
      <div class="info-row"><span class="info-label">成员数</span><span>{{ members.length }}</span></div>
      <div class="info-row"><span class="info-label">能力包</span><span>{{ capPermissions.length }} 项</span></div>
      <div class="info-row"><span class="info-label">接口权限</span><span>{{ permissions.length }} 项</span></div>
      <div class="info-row"><span class="info-label">我的身份</span><span>{{ myRole === 2 ? '组长' : '成员' }}</span></div>
    </div>

    <!-- 成员 -->
    <div class="section-title">成员</div>
    <div class="panel">
      <div v-if="isAdmin" class="panel-toolbar">
        <button class="btn btn-sm" @click="showAddMember = true">添加成员</button>
      </div>
      <table class="data-table data-table-sm">
        <thead><tr><th>ID</th><th>用户名</th><th>姓名</th><th>部门</th><th>身份</th><th v-if="isAdmin"></th></tr></thead>
        <tbody>
          <tr v-for="m in members" :key="m.id">
            <td class="mono">{{ m.id }}</td>
            <td class="mono">{{ m.username }}</td>
            <td>{{ m.display_name }}</td>
            <td class="text-secondary">{{ m.dept || '—' }}</td>
            <td><span class="tag" v-if="m.role === 2">组长</span><span v-else class="text-secondary">成员</span></td>
            <td v-if="isAdmin">
              <button v-if="m.id !== myId" class="btn btn-sm" @click="removeMember(m)">移除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="members.length === 0" class="empty-state">暂无成员</div>
    </div>

    <!-- 能力包授权（与 MyPermissions 同风格：卡片 + 抽屉） -->
    <div class="section-title">能力包授权</div>
    <div v-if="capPermissions.length === 0" class="empty-state">暂未通过能力包获得授权</div>
    <div v-else class="cap-grid">
      <div v-for="(p, i) in capPermissions" :key="p.request_id + '-' + i" class="cap-card" @click="openCapDetail(p)">
        <div class="cap-top">
          <div class="cap-icon" :class="toneOf(p)">{{ iconOf(p) }}</div>
          <div style="flex:1;min-width:0;">
            <div class="cap-name">{{ p.capability_name }}</div>
            <div class="cap-app">{{ p.app_name }} · <span class="mono">{{ p.preset_name }}</span></div>
          </div>
          <span class="tag tag-ok">已生效</span>
        </div>
        <div class="cap-desc">{{ p.description || '—' }}</div>
        <div class="cap-tags">
          <span class="tag tag-amber">👥 自建组</span>
          <span v-if="p.scope_text" class="tag tag-cyan">范围: {{ p.scope_text }}</span>
          <span class="tag tag-gray">{{ (p.interfaces || []).length }} 接口</span>
        </div>
        <div class="cap-foot">
          <span class="foot-time">{{ p.created_at }}</span>
          <span class="foot-link">查看详情 →</span>
        </div>
      </div>
    </div>

    <!-- 接口权限（直授，非能力包） -->
    <template v-if="permissions.length > 0">
      <div class="section-title">接口权限</div>
      <div class="panel">
        <div class="action-list" style="padding: 14px 16px;">
          <span v-for="a in permissions" :key="a.id" class="action-tag">{{ a.code }}</span>
        </div>
      </div>
    </template>

    <!-- 能力包详情抽屉（与 MyPermissions 风格一致） -->
    <el-drawer v-model="showCapDrawer" :title="currentCap?.capability_name || '能力包详情'" size="480px">
      <div v-if="currentCap" class="detail-view">
        <div class="dv-head">
          <div class="cap-icon big" :class="toneOf(currentCap)">{{ iconOf(currentCap) }}</div>
          <div style="flex:1;">
            <div class="dv-name">{{ currentCap.capability_name }}</div>
            <div class="dv-app">{{ currentCap.app_name }} · <span class="mono">{{ currentCap.preset_name }}</span></div>
          </div>
          <span class="tag tag-ok">已生效</span>
        </div>
        <p class="dv-desc">{{ currentCap.description || '—' }}</p>

        <div class="sec">
          <div class="sec-title">📦 能力包详情</div>
          <div class="kv"><span class="k">所属应用</span><span class="v">{{ currentCap.app_name }}</span></div>
          <div class="kv"><span class="k">权限预设</span><span class="v mono">{{ currentCap.preset_name }}</span></div>
          <div class="kv"><span class="k">作用主体</span><span class="v">👥 自建组 · {{ group?.name }}</span></div>
          <div class="kv"><span class="k">数据范围</span><span class="v">{{ currentCap.scope_text || '接口级（全部数据）' }}</span></div>
          <div class="kv"><span class="k">授权时间</span><span class="v mono">{{ currentCap.created_at }}</span></div>
          <div class="kv"><span class="k">接口权限</span><span class="v"><span v-for="op in currentCap.interfaces || []" :key="op" class="op-chip mono">{{ op }}</span></span></div>
          <div class="kv"><span class="k">授权理由</span><span class="v">{{ currentCap.reason || '—' }}</span></div>
        </div>

        <div class="sec">
          <div class="sec-title">📋 申请单</div>
          <div v-if="capReqDetail">
            <div class="req-head">
              <span class="tag tag-blue">{{ capReqDetail.request.request_type === 3 ? '接入申请' : '权限申请' }}</span>
              <span class="req-title">{{ capReqDetail.title }}</span>
              <span class="tag" :class="capReqDetail.request.status === 2 ? 'tag-ok' : 'tag-amber'">{{ statusLabel(capReqDetail.request.status) }}</span>
              <span class="req-link" @click="$router.push(`/requests/${capReqDetail.request.id}`)">完整单 →</span>
            </div>
            <div class="kv"><span class="k">单号</span><span class="v mono req-no">{{ capReqDetail.ticket_no }}</span></div>
            <div class="kv"><span class="k">风险</span><span class="v">{{ ['低', '中', '高'][capReqDetail.request.risk_level - 1] || '—' }}</span></div>
            <div class="kv"><span class="k">申请人</span><span class="v">{{ capReqDetail.applicant }}</span></div>
            <div class="kv"><span class="k">理由</span><span class="v reason">{{ capReqDetail.request.reason || '—' }}</span></div>

            <div class="timeline">
              <div class="tl-step done">
                <div class="tl-dot"></div>
                <div>
                  <div class="tl-title">发起申请 <span class="tag tag-ok">已提交</span></div>
                  <div class="tl-meta">{{ capReqDetail.applicant }} · {{ capReqDetail.request.created_at }}</div>
                </div>
              </div>
              <div v-for="(task, ti) in capReqDetail.tasks || []" :key="ti" class="tl-step" :class="task.action === 1 ? 'done' : task.action === 2 ? 'reject' : ''">
                <div class="tl-dot"></div>
                <div>
                  <div class="tl-title">{{ task.approver_name }} <span class="tag" :class="task.action === 1 ? 'tag-ok' : task.action === 2 ? 'tag-amber' : 'tag-gray'">{{ task.action === 1 ? '通过' : task.action === 2 ? '拒绝' : '待审批' }}</span></div>
                  <div class="tl-meta">{{ task.approver_role }} · {{ task.updated_at }}</div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-secondary" style="font-size:12px;">加载申请单…</div>
        </div>

        <div class="footer-actions">
          <button class="btn" @click="$router.push(`/marketplace?capability=${currentCap.capability_id}`)">📦 查看能力包</button>
          <button class="btn btn-primary" @click="$router.push('/marketplace')">🛒 去能力市场申请</button>
        </div>
      </div>
    </el-drawer>

    <el-dialog v-model="showAddMember" title="添加成员" width="420">
      <el-form label-width="70">
        <el-form-item label="用户">
          <el-select v-model="newMemberId" filterable style="width: 100%;">
            <el-option v-for="u in allUsers" :key="u.id" :label="`${u.display_name || u.username} (${u.username})`" :value="u.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn" @click="showAddMember = false">取消</button>
        <button class="btn btn-primary" @click="addMember">添加</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const route = useRoute()
const groupId = Number(route.params.id)

const group = ref<any>(null)
const members = ref<any[]>([])
const permissions = ref<any[]>([])
const capPermissions = ref<any[]>([])
const allUsers = ref<any[]>([])
const myId = ref(0)
const myRole = ref(1)
const isLeaf = ref(false)

const showAddMember = ref(false)
const newMemberId = ref<number | undefined>(undefined)

// 能力包详情抽屉
const showCapDrawer = ref(false)
const currentCap = ref<any>(null)
const capReqDetail = ref<any>(null)

const isAdmin = computed(() => myRole.value === 2 || myId.value === 1)

onMounted(load)

async function load() {
  try {
    const [groupsData, myGroups] = await Promise.all([api.groups(), api.meGroups()])
    const all = (groupsData as any).items || []
    group.value = all.find((g: any) => g.id === groupId)
    const me = await api.me()
    myId.value = (me as any).user?.id || 0

    if (group.value?.type === 2) {
      const myg = ((myGroups as any).items || []).find((g: any) => g.id === groupId)
      if (myg) {
        members.value = myg.members || []
        myRole.value = myg.my_role || 1
      }
      const gp = await api.getGroupPermissions(groupId).catch(() => ({ items: [] }))
      permissions.value = (gp as any).items || []
      const cp = await api.getGroupCapabilityPermissions(groupId).catch(() => ({ items: [] }))
      capPermissions.value = (cp as any).items || []
    } else {
      const orgData = await api.meOrgPermissions()
      const findOrg = (items: any[]): any => {
        for (const o of items || []) {
          if (o.id === groupId) return o
          const sub = findOrg(o.sub_orgs)
          if (sub) return sub
        }
        return null
      }
      const org = findOrg((orgData as any).items)
      if (org) {
        members.value = org.members || []
        permissions.value = org.permissions || []
        isLeaf.value = org.is_leaf
        myRole.value = org.is_leaf ? 2 : 1
      }
    }
    const usersData = await api.users()
    allUsers.value = (usersData as any).items || []
  } catch (e: any) { ElMessage.error(e.message) }
}

// 能力包图标/色调（与 MyPermissions 一致）
function iconOf(p: any) {
  const n = p.capability_name || ''
  if (n.includes('主机')) return '🖥️'
  if (n.includes('数据库')) return '🗄️'
  if (n.includes('容器')) return '🐳'
  if (n.includes('安全')) return '🛡️'
  if (n.includes('路由')) return '🧭'
  if (n.includes('权限')) return '🔑'
  if (n.includes('服务')) return '🧩'
  if (n.includes('环境')) return '🌍'
  return '📦'
}
function toneOf(p: any) {
  const n = p.capability_name || ''
  if (n.includes('主机')) return 'blue'
  if (n.includes('数据库')) return 'amber'
  if (n.includes('容器')) return 'cyan'
  if (n.includes('权限')) return 'violet'
  return 'green'
}
function statusLabel(s: number) {
  return ['', '待审批', '已通过', '已拒绝', '已回收'][s] || s
}

async function openCapDetail(p: any) {
  currentCap.value = p
  capReqDetail.value = null
  showCapDrawer.value = true
  try {
    capReqDetail.value = await api.requestDetail(p.request_id)
  } catch { /* ignore */ }
}

async function addMember() {
  if (!newMemberId.value) { ElMessage.warning('请选择用户'); return }
  await api.addMember(groupId, newMemberId.value)
  ElMessage.success('已添加')
  showAddMember.value = false
  load()
}

async function removeMember(m: any) {
  await api.removeMember(groupId, m.id)
  ElMessage.success('已移除')
  load()
}

function fmtDate(v: any): string { return v ? new Date(v).toLocaleString('zh-CN', { hour12: false }) : '' }
</script>

<style scoped>
.group-detail-page { max-width: 1200px; }
.back-link { font-size: 12px; color: var(--text-secondary); text-decoration: none; font-family: var(--font-mono); }
.back-link:hover { color: var(--text); }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; letter-spacing: -0.5px; margin: 6px 0 4px; }
.page-desc { font-size: 13px; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }

.panel { border: 1px solid var(--border); background: var(--bg); }
.panel-toolbar { display: flex; justify-content: flex-end; padding: 10px 16px; border-bottom: 1px solid var(--border); }
.section-title { font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-family: var(--font-mono); color: var(--text-secondary); margin: 24px 0 8px; }

.info-panel { display: flex; flex-wrap: wrap; gap: 24px; padding: 14px 16px; }
.info-row { display: flex; gap: 8px; font-size: 13px; }
.info-label { color: var(--text-secondary); font-size: 12px; }

.btn { padding: 6px 16px; font-size: 12px; font-weight: 600; border: 1px solid var(--border); background: var(--bg); color: var(--text); cursor: pointer; transition: all 0.15s; font-family: var(--font-mono); }
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn-primary { background: var(--accent); color: var(--accent-text); border-color: var(--accent); }
.btn-primary:hover { opacity: 0.9; }
.btn-sm { padding: 4px 12px; font-size: 11px; }

.data-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.data-table th { text-align: left; padding: 10px 16px; font-family: var(--font-mono); font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--text-secondary); background: var(--bg-secondary); border-bottom: 1px solid var(--border); }
.data-table td { padding: 10px 16px; border-bottom: 1px solid var(--border); }
.data-table-sm th, .data-table-sm td { padding: 8px 12px; font-size: 12px; }

.action-list { display: flex; flex-wrap: wrap; gap: 6px; }
.action-tag { font-family: var(--font-mono); font-size: 11px; padding: 3px 8px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; }

/* 能力包卡片网格（与 MyPermissions 风格一致） */
.cap-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.cap-card { border: 1px solid var(--border); border-radius: 14px; padding: 18px; background: var(--bg-card); cursor: pointer; transition: box-shadow .2s, border-color .2s, transform .2s; }
.cap-card:hover { border-color: var(--brand); box-shadow: 0 4px 12px rgba(0,0,0,0.08); transform: translateY(-2px); }
.cap-top { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.cap-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.cap-icon.blue { background: var(--brand-soft, #eaf1fe); }
.cap-icon.amber { background: var(--warning-bg, #fef3c7); }
.cap-icon.cyan { background: var(--info-bg, #cffafe); }
.cap-icon.violet { background: var(--purple-bg, #ede9fe); }
.cap-icon.green { background: var(--success-bg, #dcfce7); }
.cap-icon.big { width: 52px; height: 52px; font-size: 24px; }
.cap-name { font-size: 16px; font-weight: 700; }
.cap-app { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }
.cap-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.cap-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.cap-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--border); }
.foot-time { font-size: 12px; color: var(--text-tertiary); }
.foot-link { font-size: 13px; color: var(--brand); font-weight: 600; }

/* 抽屉详情（与 MyPermissions 风格一致） */
.detail-view { padding: 0 4px; }
.dv-head { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.dv-name { font-size: 18px; font-weight: 700; }
.dv-app { font-size: 13px; color: var(--text-tertiary); margin-top: 2px; }
.dv-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 20px; line-height: 1.6; }
.sec { margin-bottom: 24px; }
.sec-title { font-size: 13px; font-weight: 700; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.sec-sub { font-size: 12px; font-weight: 600; color: var(--text-secondary); margin: 16px 0 8px; }
.kv { display: flex; gap: 12px; font-size: 13px; margin-bottom: 8px; }
.kv .k { color: var(--text-secondary); min-width: 70px; flex-shrink: 0; }
.kv .v { color: var(--text); word-break: break-all; }
.op-chip { display: inline-block; padding: 2px 8px; margin: 2px 4px; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 4px; font-size: 11px; }
.req-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.req-title { font-weight: 600; font-size: 14px; }
.req-no { color: var(--brand); }
.req-link { margin-left: auto; font-size: 12px; color: var(--brand); cursor: pointer; font-weight: 600; }
.req-link:hover { text-decoration: underline; }
.reason { font-style: italic; color: var(--text-secondary); }
.footer-actions { display: flex; gap: 10px; margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border); }

/* 时间线 */
.timeline { margin: 16px 0; padding-left: 20px; }
.tl-step { position: relative; padding-left: 24px; padding-bottom: 20px; border-left: 2px solid var(--border); }
.tl-step:last-child { border-left-color: transparent; }
.tl-dot { position: absolute; left: -9px; top: 2px; width: 16px; height: 16px; border-radius: 50%; background: var(--bg-tertiary); border: 2px solid var(--border); }
.tl-step.done .tl-dot { background: var(--success, #16a34a); border-color: var(--success, #16a34a); }
.tl-step.reject .tl-dot { background: #ef4444; border-color: #ef4444; }
.tl-title { font-size: 13px; font-weight: 600; }
.tl-meta { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

.expr-toggle { font-size: 12px; color: var(--brand); cursor: pointer; margin-bottom: 8px; }
.expr { font-family: var(--font-mono); font-size: 12px; padding: 10px 14px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 6px; white-space: pre-wrap; word-break: break-all; }

.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: rgba(34,197,94,0.12); color: #16a34a; }
.tag-blue { background: rgba(59,130,246,0.12); color: #2563eb; }
.tag-amber { background: rgba(245,158,11,0.12); color: #d97706; }
.tag-cyan { background: rgba(6,182,212,0.12); color: #0891b2; }
.tag-gray { background: rgba(156,163,175,0.15); color: #6b7280; }
.tag-violet { background: rgba(139,92,246,0.12); color: #7c3aed; }
.tag-org { background: rgba(59,130,246,0.15); color: #3b82f6; }
.tag-custom { background: rgba(168,85,247,0.15); color: #a855f7; }
.tag-leaf { background: rgba(34,197,94,0.15); color: #22c55e; }
.tag-ro { background: rgba(100,116,139,0.2); color: var(--text-secondary); }

.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
.empty-state { padding: 32px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
