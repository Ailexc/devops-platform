<template>
  <div class="stat-card" :class="`tone-${tone}`" @click="$emit('click')">
    <div class="stat-icon" v-html="icon"></div>
    <div>
      <div class="stat-value">{{ value }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ icon: string; value: string | number; label: string; tone?: 'blue' | 'green' | 'amber' | 'violet' }>(), { tone: 'blue' })
defineEmits<{ (e: 'click'): void }>()
</script>

<style scoped>
.stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; box-shadow: var(--shadow-sm); display: flex; gap: 14px; align-items: center; cursor: pointer; transition: box-shadow .2s, transform .2s; }
.stat-card:hover { box-shadow: var(--shadow-md); transform: translateY(-2px); }
.stat-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 18px; }
.stat-icon :deep(svg) { width: 20px; height: 20px; stroke: currentColor; }
.tone-blue .stat-icon { background: var(--brand-soft); color: var(--brand); }
.tone-green .stat-icon { background: var(--success-bg); color: var(--success); }
.tone-amber .stat-icon { background: var(--warning-bg); color: var(--warning); }
.tone-violet .stat-icon { background: var(--purple-bg); color: var(--purple); }
.stat-value { font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; line-height: 1.2; }
.stat-label { font-size: 12px; color: var(--text-secondary); }
</style>
