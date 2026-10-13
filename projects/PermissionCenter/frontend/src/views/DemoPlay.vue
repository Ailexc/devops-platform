<template>
  <!-- 目录页 -->
  <div v-if="!currentSlug" class="demo-root">
    <ScenarioCatalog @start="goToScenario" />
  </div>

  <!-- 播放页 -->
  <div v-else class="demo-play" @keydown="onKeydown" tabindex="0" ref="container">
    <!-- 顶部横条：全宽 -->
    <div class="play-header">
      <div class="ph-left">
        <button class="back-btn" @click="router.push('/')" title="返回主菜单">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22V12h6v10"/></svg>
          主菜单
        </button>
        <button class="back-btn" @click="router.push('/demo')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
          返回目录
        </button>
      </div>
      <div class="ph-center">
        <h2 class="ph-title">{{ activeScenario.title }}</h2>
        <span class="ph-step-badge">步骤 {{ stepIndex + 1 }} / {{ activeSteps.length }}</span>
      </div>
      <div class="ph-right">
        <div class="ph-role-avatar" :class="{ 'ph-role-system': activeStep.role === '—' }">
          {{ activeStep.role === '—' ? '🌐' : activeStep.role.slice(0, 1) }}
        </div>
        <div class="ph-role-info">
          <span class="ph-role-name">{{ activeStep.role === '—' ? '系统' : activeStep.role }}</span>
          <span class="ph-role-desc">{{ activeStep.roleLabel }}</span>
        </div>
      </div>
    </div>

    <!-- dual 模式 tab 切换 -->
    <div v-if="currentSlug === 'dual'" class="dual-tabs">
      <button class="dtab" :class="{ active: dualSub === 'xiaohuang' }" @click="switchDualSub('xiaohuang')">👤 小黄（应用 Owner）</button>
      <button class="dtab" :class="{ active: dualSub === 'xiaohong' }" @click="switchDualSub('xiaohong')">🔑 小红（权限申请者）</button>
    </div>

    <!-- 下方主体：侧栏 + 内容区 是一个整体 -->
    <div class="play-body">
      <StepSidebar
        :scenarioTitle="activeScenario.title"
        :steps="activeSteps"
        :currentIndex="stepIndex"
        @goto="goToStep"
      />

      <div class="player-area">
        <div class="screen-viewport">
          <transition :name="transitionName" mode="out-in">
            <component :is="screenComponent" :key="currentSlug + '-' + dualSub + '-' + stepIndex" />
          </transition>
        </div>

        <div class="narration-bar">
          <div class="narration-text">{{ activeStep.narration }}</div>
        </div>

        <PlayerControls
          :stepIndex="stepIndex"
          :total="activeSteps.length"
          :isAutoPlaying="isAutoPlaying"
          :hasPrevScenario="hasPrevScenario"
          :hasNextScenario="hasNextScenario"
          @prev="prev"
          @next="next"
          @reset="reset"
          @toggleAutoPlay="toggleAutoPlay"
          @prevScenario="prevScenario"
          @nextScenario="nextScenario"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ScenarioCatalog from '../components/demo/ScenarioCatalog.vue'
import PlayerControls from '../components/demo/PlayerControls.vue'
import StepSidebar from '../components/demo/StepSidebar.vue'
// 场景 1&2: 双视角
import LoginScreen from '../components/demo/screens/LoginScreen.vue'
import WorkbenchScreen from '../components/demo/screens/WorkbenchScreen.vue'
import CapEditorScreen from '../components/demo/screens/CapEditorScreen.vue'
import PresetConfigScreen from '../components/demo/screens/PresetConfigScreen.vue'
import AuthzMgmtScreen from '../components/demo/screens/AuthzMgmtScreen.vue'
import ApprovalFlowScreen from '../components/demo/screens/ApprovalFlowScreen.vue'
import StatusConfirmScreen from '../components/demo/screens/StatusConfirmScreen.vue'
import CompleteScreen from '../components/demo/screens/CompleteScreen.vue'
import MarketplaceScreen from '../components/demo/screens/MarketplaceScreen.vue'
import PresetSelectScreen from '../components/demo/screens/PresetSelectScreen.vue'
import SubjectSelectScreen from '../components/demo/screens/SubjectSelectScreen.vue'
import SubmitConfirmScreen from '../components/demo/screens/SubmitConfirmScreen.vue'
import SwitchUserScreen from '../components/demo/screens/SwitchUserScreen.vue'
import ApprovalScreen from '../components/demo/screens/ApprovalScreen.vue'
import VerifyScreen from '../components/demo/screens/VerifyScreen.vue'
import DataScopeScreen from '../components/demo/screens/DataScopeScreen.vue'
// 场景 4: 策略与授权
import ApprovalChainScreen from '../components/demo/screens/ApprovalChainScreen.vue'
// 场景 5: 审计与观测
import TraceScreen from '../components/demo/screens/TraceScreen.vue'
import PEPResolverScreen from '../components/demo/screens/PEPResolverScreen.vue'
import AuditLogScreen from '../components/demo/screens/AuditLogScreen.vue'
import ObsCacheScreen from '../components/demo/screens/ObsCacheScreen.vue'
import ObsMetricsScreen from '../components/demo/screens/ObsMetricsScreen.vue'
import ObsOwnersScreen from '../components/demo/screens/ObsOwnersScreen.vue'
// 场景 6: 端到端
import GatewayCheckScreen from '../components/demo/screens/GatewayCheckScreen.vue'
// 场景 7: 架构总结
import ArchSummaryScreen from '../components/demo/screens/ArchSummaryScreen.vue'
// 场景 2: 个人权限板块
import PermWorkbenchScreen from '../components/demo/screens/PermWorkbenchScreen.vue'
import PermDimensionsScreen from '../components/demo/screens/PermDimensionsScreen.vue'
import PermOrgDetailScreen from '../components/demo/screens/PermOrgDetailScreen.vue'
import PermCalcScreen from '../components/demo/screens/PermCalcScreen.vue'
import PermAuditTrailScreen from '../components/demo/screens/PermAuditTrailScreen.vue'
import PermSummaryScreen from '../components/demo/screens/PermSummaryScreen.vue'
// 场景 3: 策略与授权
import PolicyTriggerScreen from '../components/demo/screens/PolicyTriggerScreen.vue'
import PolicyCreatedScreen from '../components/demo/screens/PolicyCreatedScreen.vue'
import PolicyEnforceScreen from '../components/demo/screens/PolicyEnforceScreen.vue'
import PolicyRevokeScreen from '../components/demo/screens/PolicyRevokeScreen.vue'
import PolicySummaryScreen from '../components/demo/screens/PolicySummaryScreen.vue'
// 场景 5: 端到端
import E2ERegisterScreen from '../components/demo/screens/E2ERegisterScreen.vue'
import E2EPublishScreen from '../components/demo/screens/E2EPublishScreen.vue'
import E2EApplyScreen from '../components/demo/screens/E2EApplyScreen.vue'
import E2EOverviewScreen from '../components/demo/screens/E2EOverviewScreen.vue'
import PermMarketScreen from '../components/demo/screens/PermMarketScreen.vue'

const screenMap: Record<string, any> = {
  LoginScreen, WorkbenchScreen, CapEditorScreen, PresetConfigScreen,
  AuthzMgmtScreen, ApprovalFlowScreen, StatusConfirmScreen, CompleteScreen,
  MarketplaceScreen, PresetSelectScreen, SubjectSelectScreen, SubmitConfirmScreen,
  SwitchUserScreen, ApprovalScreen, VerifyScreen, DataScopeScreen,
  ApprovalChainScreen, TraceScreen, PEPResolverScreen, AuditLogScreen,
  ObsCacheScreen, ObsMetricsScreen, ObsOwnersScreen,
  GatewayCheckScreen, ArchSummaryScreen,
  PermWorkbenchScreen, PermDimensionsScreen, PermOrgDetailScreen,
  PermCalcScreen, PermAuditTrailScreen, PermSummaryScreen,
  PolicyTriggerScreen, PolicyCreatedScreen, PolicyEnforceScreen,
  PolicyRevokeScreen, PolicySummaryScreen,
  E2ERegisterScreen, E2EPublishScreen, E2EApplyScreen, E2EOverviewScreen,
  PermMarketScreen,
}

interface Step { component: string; title?: string; role: string; roleLabel: string; narration: string; animation: string }

// ── 双视角子场景 ──
const dualScenarios: Record<string, Step[]> = {
  xiaohuang: [
    { component: 'LoginScreen', title: '小黄登录', role: '—', roleLabel: '访客', narration: '应用 Owner 小黄登录权限中心', animation: 'fade' },
    { component: 'WorkbenchScreen', title: '工作台', role: '小黄', roleLabel: '应用 Owner', narration: '进入工作台，选择自己负责的应用「小黄的监控服务」', animation: 'slide-left' },
    { component: 'CapEditorScreen', title: '能力编辑', role: '小黄', roleLabel: '应用 Owner', narration: '打包能力「主机监控」：绑定只读接口 + 配置数据范围控制（按环境/地域/实例）', animation: 'slide-left' },
    { component: 'PresetConfigScreen', title: '预设配置', role: '小黄', roleLabel: '应用 Owner', narration: '配置预设「只读监控」，设定组织/人员可申请范围', animation: 'slide-left' },
    { component: 'AuthzMgmtScreen', title: '授权管理', role: '小黄', roleLabel: '应用 Owner', narration: '进入授权管理，点击「上架」按钮发布到能力市场', animation: 'slide-left' },
    { component: 'ApprovalFlowScreen', title: '审批流程', role: '系统', roleLabel: '审批流程', narration: '走审批流程 → Owner 确认 → 平台复核 → 审批通过', animation: 'pop-in' },
    { component: 'StatusConfirmScreen', title: '状态确认', role: '小黄', roleLabel: '应用 Owner', narration: '预设状态已变为 published，能力市场已可见', animation: 'slide-left' },
    { component: 'CompleteScreen', title: '完成', role: '—', roleLabel: '完成', narration: '✅ 小黄的发布流程完成：声明 → 配置 → 上架 → 审批', animation: 'celebrate' },
  ],
  xiaohong: [
    { component: 'LoginScreen', title: '小红登录', role: '—', roleLabel: '访客', narration: '普通用户小红登录权限中心', animation: 'fade' },
    { component: 'MarketplaceScreen', title: '能力市场', role: '小红', roleLabel: '权限申请者', narration: '进入能力市场，发现小黄发布的「主机监控」能力', animation: 'slide-left' },
    { component: 'PresetSelectScreen', title: '选择预设', role: '小红', roleLabel: '权限申请者', narration: '选择「只读监控」预设，查看包含的接口权限', animation: 'slide-left' },
    { component: 'SubjectSelectScreen', title: '选择主体', role: '小红', roleLabel: '权限申请者', narration: '选择双主体：👤 小红（人）+ 🔌 小红的数据分析（程序）', animation: 'slide-left' },
    { component: 'DataScopeScreen', title: '数据范围', role: '小红', roleLabel: '权限申请者', narration: '选择数据范围：生产环境 + 华北/华南地域，精确控制数据访问边界', animation: 'slide-left' },
    { component: 'SubmitConfirmScreen', title: '提交申请', role: '小红', roleLabel: '权限申请者', narration: '填写理由「需要读取生产环境主机」，提交申请', animation: 'slide-left' },
    { component: 'SwitchUserScreen', title: '切换视角', role: '小黄', roleLabel: '应用 Owner', narration: '切换到小黄视角，审批中心看到待审批工单', animation: 'slide-left' },
    { component: 'ApprovalScreen', title: '审批通过', role: '小黄', roleLabel: '应用 Owner', narration: '审批通过 → 策略立即生效 → 授权完成', animation: 'pop-in' },
    { component: 'VerifyScreen', title: '权限验证', role: '—', roleLabel: '验证', narration: '✅ 权限验证：GET 主机 200 ✅ / POST 主机 403 🚫', animation: 'celebrate' },
  ],
}

// ── 所有场景定义 ──
const allScenarios: Record<string, { title: string; steps: Step[] }> = {
  dual: { title: '双视角演示', steps: [] }, // 特殊：用 dualScenarios
  org: {
    title: '个人权限板块',
    steps: [
      { component: 'PermWorkbenchScreen', title: '工作台总览', role: 'bob', roleLabel: '普通用户', narration: 'bob 的工作台：四维权限统计（组织/个人/自建组/应用）', animation: 'fade' },
      { component: 'PermDimensionsScreen', title: '三维度权限', role: 'bob', roleLabel: '普通用户', narration: '我的权限页面（能力包维度）：个人权限 3 个 / 组织权限 1 个 / 自建组权限 4 个', animation: 'slide-left' },
      { component: 'PermOrgDetailScreen', title: '组织权限详解', role: 'bob', roleLabel: '普通用户', narration: '组织权限来自组织树继承：总公司→研发中心→研发一部，组即角色自动生效', animation: 'slide-left' },
      { component: 'PermCalcScreen', title: '权限计算', role: '—', roleLabel: '系统', narration: '三维度取并集：个人权限 ∪ 组织权限 ∪ 自建组权限 = 最终权限', animation: 'pop-in' },
      { component: 'PermAuditTrailScreen', title: '授权来源', role: 'bob', roleLabel: '普通用户', narration: '每条权限关联申请单：组织权限来自组长申请，个人权限来自个人申请', animation: 'slide-left' },
      { component: 'PermSummaryScreen', title: '总结', role: '—', roleLabel: '完成', narration: '✅ 个人权限：三维度并集 + 申请单留痕 + TTL 自动回收 + 审批链 SoD', animation: 'celebrate' },
    ],
  },
  policy: {
    title: '授权与策略',
    steps: [
      { component: 'PolicyTriggerScreen', title: '策略触发', role: '—', roleLabel: '系统视角', narration: '策略不是手动创建的，而是由上架预设或用户申请自动触发', animation: 'fade' },
      { component: 'PolicyCreatedScreen', title: '策略生成', role: '系统', roleLabel: '自动创建', narration: '审批通过瞬间：Casbin 动作级策略 + OpenFGA 实例级关系元组自动生成', animation: 'slide-left' },
      { component: 'PolicyEnforceScreen', title: '策略执行', role: '系统', roleLabel: 'Traefik PEP', narration: '网关实时鉴权：Casbin 校验动作权限 → OpenFGA 过滤数据范围 → 读允许/写拒绝', animation: 'slide-left' },
      { component: 'PolicyRevokeScreen', title: '策略回收', role: '小黄', roleLabel: '应用 Owner', narration: '下架预设 / 回收授权 → 策略删除 → OpenFGA 关系撤销 → 权限即时失效', animation: 'pop-in' },
      { component: 'ApprovalChainScreen', title: '审批与SoD', role: 'admin', roleLabel: '系统管理员', narration: '多级审批链 + SoD 职责分离：申请人≠审批人，高风险追加安全复核', animation: 'slide-left' },
      { component: 'PolicySummaryScreen', title: '总结', role: '—', roleLabel: '完成', narration: '✅ 策略全生命周期：触发→审批→生效→执行→回收，审批即策略无死角', animation: 'celebrate' },
    ],
  },
  audit: {
    title: '审计与观测',
    steps: [
      { component: 'LoginScreen', title: '管理员登录', role: 'admin', roleLabel: '系统管理员', narration: '管理员登录系统观测平台', animation: 'fade' },
      { component: 'TraceScreen', title: '链路追踪', role: 'admin', roleLabel: '系统管理员', narration: '每个请求生成 TraceID，PEP→PDP 决策全链路可视化', animation: 'slide-left' },
      { component: 'PEPResolverScreen', title: 'PEP 解析', role: 'admin', roleLabel: '系统管理员', narration: '请求→action 映射→策略匹配，步骤化可视化', animation: 'slide-left' },
      { component: 'AuditLogScreen', title: '决策日志', role: 'admin', roleLabel: '系统管理员', narration: '决策日志含 TraceID，与链路追踪联动，全链路溯源', animation: 'slide-left' },
      { component: 'ObsCacheScreen', title: '决策缓存', role: 'admin', roleLabel: '系统管理员', narration: '决策缓存工作台：authz:dec:* 键 + 命中率 + 一键失效，策略变更不生效时首要排查', animation: 'slide-left' },
      { component: 'ObsMetricsScreen', title: '指标面板', role: 'admin', roleLabel: '系统管理员', narration: '鉴权指标面板：决策量 / 允许拒绝 / 延迟百分位 / 24h 趋势 / Top 权限点', animation: 'slide-left' },
      { component: 'ObsOwnersScreen', title: 'Owner 巡检', role: 'admin', roleLabel: '系统管理员', narration: 'Owner 巡检：失联 owner 提醒 → 达阈值自动停用 → 新 owner 认领恢复', animation: 'slide-left' },
      { component: 'CompleteScreen', title: '完成', role: '—', roleLabel: ' 完成', narration: '✅ 可观测：TraceID 贯穿 + 决策缓存 / 指标面板 / Owner 巡检，黑盒显性化', animation: 'celebrate' },
    ],
  },
  e2e: {
    title: '端到端完整链路',
    steps: [
      { component: 'E2ERegisterScreen', title: '注册应用', role: '小黄', roleLabel: '应用 Owner', narration: '应用注册三步走：基础信息 → 鉴权方式注册（Client Credentials）→ 网络信息登记', animation: 'fade' },
      { component: 'E2EPublishScreen', title: '发布能力', role: '小黄', roleLabel: '应用 Owner', narration: '声明能力 → 配置预设（接口绑定+数据范围+可申请主体）→ 上架市场', animation: 'slide-left' },
      { component: 'E2EApplyScreen', title: '申请能力', role: 'bob', roleLabel: '权限申请者', narration: 'Step 3：用户在能力市场浏览 → 选预设 → 选主体 → 数据范围 → 提交', animation: 'slide-left' },
      { component: 'ApprovalScreen', title: '审批授权', role: '小黄', roleLabel: '应用 Owner', narration: 'Step 4：多级审批 → SoD 职责分离 → 策略自动创建 → 权限生效', animation: 'pop-in' },
      { component: 'GatewayCheckScreen', title: '网关鉴权', role: '系统', roleLabel: 'Traefik PEP', narration: 'Step 5：Casbin 动作级 + OpenFGA 实例级双引擎实时校验', animation: 'slide-left' },
      { component: 'TraceScreen', title: '审计追踪', role: 'admin', roleLabel: '系统管理员', narration: 'Step 6：TraceID 贯穿全链路，从请求到决策完整溯源', animation: 'slide-left' },
      { component: 'E2EOverviewScreen', title: '链路总结', role: '—', roleLabel: '完成', narration: '✅ 端到端：注册→发布→申请→审批→鉴权→审计，系统核心能力一气呵成', animation: 'celebrate' },
    ],
  },
  arch: {
    title: '系统概览',
    steps: [
      { component: 'PermWorkbenchScreen', title: '工作台', role: 'admin', roleLabel: '系统管理员', narration: '去中心化工作台 — 以「我」为中心的权限视图，四维统计一目了然', animation: 'fade' },
      { component: 'PermDimensionsScreen', title: '个人权限', role: 'bob', roleLabel: '普通用户', narration: '板块一：个人权限 — 个人/组织/自建组三维度权限并集', animation: 'slide-left' },
      { component: 'E2ERegisterScreen', title: '应用管理', role: '小黄', roleLabel: '应用 Owner', narration: '板块二：应用管理 — 注册应用，声明身份和负责人（≥2人）', animation: 'slide-left' },
      { component: 'CapEditorScreen', title: '打包能力', role: '小黄', roleLabel: '应用 Owner', narration: '板块三：打包能力 — 声明接口 + 配置数据范围控制 + 预设 + 上架市场', animation: 'slide-left' },
      { component: 'PermMarketScreen', title: '权限市场', role: 'bob', roleLabel: '权限申请者', narration: '板块四：权限市场 — 应用授权（鉴权+网络打通）→ 能力包申请（接口+数据范围）', animation: 'slide-left' },
      { component: 'TraceScreen', title: '审计与观测', role: 'admin', roleLabel: '系统管理员', narration: '板块五：审计与观测 — 链路追踪 / PEP 解析 / 决策缓存 / 指标面板 / 数据面图谱 / Owner 巡检，全链路可观测', animation: 'slide-left' },
      { component: 'ArchSummaryScreen', title: '架构总结', role: '—', roleLabel: '总结', narration: '🏗️ PEP/PDP/PAP/PIP 四平面 + 去中心化 IAM 六大设计理念', animation: 'celebrate' },
    ],
  },
}

const scenarioOrder = ['arch', 'org', 'e2e', 'policy', 'audit', 'dual']

const route = useRoute()
const router = useRouter()
const currentSlug = ref((route.params.slug as string) || '')
const dualSub = ref('xiaohuang')
const stepIndex = ref(0)
const isAutoPlaying = ref(false)
const transitionName = ref('slide-left')
const container = ref<HTMLElement | null>(null)
let autoTimer: ReturnType<typeof setInterval> | null = null

const activeScenario = computed(() => allScenarios[currentSlug.value] || { title: '', steps: [] })

// dual 模式下，activeSteps 根据 dualSub 切换
const activeSteps = computed(() => {
  if (currentSlug.value === 'dual') return dualScenarios[dualSub.value] || []
  return activeScenario.value.steps
})
const activeStep = computed(() => activeSteps.value[stepIndex.value] || { component: 'LoginScreen', role: '', roleLabel: '', narration: '', animation: 'fade' })
const screenComponent = computed(() => screenMap[activeStep.value.component])

// 场景导航
const currentScenarioIdx = computed(() => scenarioOrder.indexOf(currentSlug.value))
const hasPrevScenario = computed(() => currentScenarioIdx.value > 0)
const hasNextScenario = computed(() => currentScenarioIdx.value < scenarioOrder.length - 1)

function goToScenario(slug: string) {
  router.push(`/demo/${slug}`)
}

function goToStep(i: number) {
  transitionName.value = i > stepIndex.value ? 'slide-left' : 'slide-right'
  stepIndex.value = i
  stopAutoPlay()
}

function next() {
  if (stepIndex.value < activeSteps.value.length - 1) {
    transitionName.value = 'slide-left'
    stepIndex.value++
  } else {
    stopAutoPlay()
  }
}

function prev() {
  if (stepIndex.value > 0) {
    transitionName.value = 'slide-right'
    stepIndex.value--
  }
}

function reset() {
  transitionName.value = 'fade'
  stepIndex.value = 0
  stopAutoPlay()
}

function switchDualSub(sub: string) {
  if (sub === dualSub.value) return
  transitionName.value = 'fade'
  dualSub.value = sub
  stepIndex.value = 0
  stopAutoPlay()
}

function prevScenario() {
  if (hasPrevScenario.value) goToScenario(scenarioOrder[currentScenarioIdx.value - 1])
}

function nextScenario() {
  if (hasNextScenario.value) goToScenario(scenarioOrder[currentScenarioIdx.value + 1])
}

function toggleAutoPlay() {
  if (isAutoPlaying.value) { stopAutoPlay() }
  else { isAutoPlaying.value = true; autoTimer = setInterval(() => next(), 4000) }
}

function stopAutoPlay() {
  isAutoPlaying.value = false
  if (autoTimer) { clearInterval(autoTimer); autoTimer = null }
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'ArrowRight' || e.key === ' ') { e.preventDefault(); next() }
  else if (e.key === 'ArrowLeft') { e.preventDefault(); prev() }
  else if (e.key === 'r' || e.key === 'R') { reset() }
  else if (e.key === 'Escape') { router.push('/demo') }
}

// 监听路由变化
watch(() => route.params.slug, (s) => {
  currentSlug.value = (s as string) || ''
  stepIndex.value = 0
  dualSub.value = 'xiaohuang'
  stopAutoPlay()
  container.value?.focus()
})

onMounted(() => { container.value?.focus() })
onUnmounted(() => { stopAutoPlay() })
</script>

<style scoped>
.demo-root { height: 100vh; overflow: auto; background: var(--bg); }
.demo-play { height: 100vh; outline: none; background: var(--bg); display: flex; flex-direction: column; }
.play-body { display: flex; flex: 1; min-height: 0; }

/* dual 模式 tab */
.dual-tabs { display: flex; gap: 8px; padding: 10px 16px 0; flex-shrink: 0; }
.dtab { padding: 7px 16px; border: 1.5px solid var(--border); border-radius: 8px; background: var(--bg-card); color: var(--text-secondary); font-size: 13px; font-weight: 500; cursor: pointer; transition: all 0.15s; }
.dtab:hover { border-color: var(--brand); color: var(--brand); }
.dtab.active { border-color: var(--brand); background: var(--brand); color: #fff; }

.player-area { flex: 1; display: flex; flex-direction: column; padding: 0 16px 16px; gap: 0; min-height: 0; }

/* ── 三栏头部 ── */
.play-header {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  min-height: 52px;
}
.ph-left { flex-shrink: 0; }
.ph-center { flex: 1; display: flex; align-items: center; justify-content: center; gap: 10px; }
.ph-right { flex-shrink: 0; display: flex; align-items: center; gap: 10px; }

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.back-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
  background: var(--brand-softer);
}

.ph-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}
.ph-step-badge {
  font-size: 12px;
  font-weight: 500;
  color: var(--brand);
  background: var(--brand-soft);
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
}

.ph-role-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--brand-soft);
  border: 2px solid var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  flex-shrink: 0;
}
.ph-role-avatar.ph-role-system {
  background: var(--bg-tertiary);
  border-color: var(--border);
}
.ph-role-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.ph-role-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.2;
}
.ph-role-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  line-height: 1.2;
}
.screen-viewport { flex: 1; display: flex; flex-direction: column; background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius) var(--radius) 0 0; overflow: hidden; position: relative; min-height: 0; }
.narration-bar { background: var(--bg-secondary); border-left: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 10px 16px; display: flex; align-items: center; gap: 8px; }
.narration-bar::before { content: '📝'; font-size: 14px; flex-shrink: 0; }
.narration-text { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }

/* 过渡动画 */
.slide-left-enter-active, .slide-left-leave-active, .slide-right-enter-active, .slide-right-leave-active { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-left-enter-from { opacity: 0; transform: translateX(30px); }
.slide-left-leave-to { opacity: 0; transform: translateX(-30px); }
.slide-right-enter-from { opacity: 0; transform: translateX(-30px); }
.slide-right-leave-to { opacity: 0; transform: translateX(30px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.pop-in-enter-active { transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1); }
.pop-in-leave-active { transition: all 0.2s ease; }
.pop-in-enter-from { opacity: 0; transform: scale(0.88); }
.pop-in-leave-to { opacity: 0; transform: scale(0.95); }
</style>
