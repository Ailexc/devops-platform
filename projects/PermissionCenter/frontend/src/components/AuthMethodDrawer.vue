<template>
  <el-drawer v-model="show" :title="method?.name || '鉴权方式'" size="480px" :with-header="true">
    <div v-if="method && k" class="auth-doc">
      <div class="doc-head">
        <span class="auth-icon">{{ method.icon }}</span>
        <div>
          <div class="doc-name">{{ method.name }}</div>
          <div class="mono text-secondary">{{ method.type }}</div>
        </div>
        <span class="tag" :class="method.strength === 'high' ? 'tag-ok' : method.strength === 'medium' ? 'tag-warn' : ''">{{ method.strengthLabel }}</span>
      </div>
      <p class="doc-desc">{{ method.desc }}</p>

      <div class="sec">
        <div class="sec-title">🔄 全流程（接入 → 使用）</div>
        <div class="flow">
          <div v-for="(f, i) in k.flow" :key="i" class="flow-step">
            <div class="fs-num">{{ i + 1 }}</div>
            <div><div class="fs-title">{{ f.step }}</div><div class="fs-desc">{{ f.desc }}</div></div>
          </div>
        </div>
      </div>

      <div class="sec"><div class="sec-title">⚙️ 运作机制</div><p class="sec-body">{{ k.mechanism }}</p></div>
      <div class="sec"><div class="sec-title">🏛️ 谁签发 · 如何签发</div><p class="sec-body">{{ k.issuer }}</p></div>
      <div class="sec">
        <div class="sec-title">🔧 使用方如何使用</div>
        <ol class="sec-list"><li v-for="(u, i) in k.usage" :key="i">{{ u }}</li></ol>
      </div>
      <div class="sec"><div class="sec-title">🔗 与权限中心的关系</div><p class="sec-body">{{ k.relation }}</p></div>
      <div class="sec"><div class="sec-title">⏳ 凭证生命周期</div><p class="sec-body">{{ k.lifecycle }}</p></div>
      <div class="sec risk"><div class="sec-title">⚠️ 风险提示</div><p class="sec-body">{{ k.risk }}</p></div>

      <div class="real-note">🏭 真实场景：生产环境凭证签发会发起到公司工单平台（OA/ITSM），办理完成后由权限中心回写激活；本系统当前为内部模拟，已预留 webhook 接口。</div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { authKnowledge } from '../views/auth-methods'

const props = defineProps<{ modelValue: boolean; method: any }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
const show = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})
const k = computed(() => (props.method ? authKnowledge(props.method.type) : null))
</script>

<style scoped>
.auth-doc { padding: 0 4px; }
.doc-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.auth-icon { font-size: 24px; }
.doc-name { font-size: 16px; font-weight: 700; }
.doc-desc { font-size: 13px; color: var(--text-secondary); margin-bottom: 18px; }
.sec { margin-bottom: 18px; }
.sec-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
.sec-body { font-size: 13px; color: var(--text-secondary); line-height: 1.7; }
.sec-list { padding-left: 18px; font-size: 13px; color: var(--text-secondary); line-height: 1.8; }
.sec.risk .sec-title { color: var(--warning); }
.flow { border-left: 2px solid var(--border); padding-left: 14px; }
.flow-step { display: flex; gap: 10px; padding: 8px 0; position: relative; }
.fs-num { width: 22px; height: 22px; border-radius: 50%; background: var(--brand-soft); color: var(--brand-strong); font-size: 11px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.fs-title { font-size: 13px; font-weight: 600; }
.fs-desc { font-size: 12px; color: var(--text-secondary); }
.real-note { margin-top: 8px; padding: 12px 14px; border-radius: 8px; background: var(--brand-softer); border: 1px solid rgba(47,111,237,.25); font-size: 12px; color: var(--brand-strong); line-height: 1.7; }
.tag { font-family: var(--font-mono); font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
.tag-ok { background: var(--success-bg); color: var(--success); }
.tag-warn { background: var(--warning-bg); color: var(--warning); }
.mono { font-family: var(--font-mono); font-size: 12px; }
.text-secondary { color: var(--text-secondary); }
</style>
