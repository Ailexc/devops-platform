<template>
  <section class="panel-card" :class="{ pad: padded }">
    <header v-if="title || $slots.actions" class="panel-head">
      <div class="panel-title">
        <slot name="title">{{ title }}</slot>
        <span v-if="sub" class="panel-sub">{{ sub }}</span>
      </div>
      <div v-if="$slots.actions" class="panel-actions"><slot name="actions" /></div>
    </header>
    <div class="panel-body" :class="{ pad: padded }"><slot /></div>
  </section>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ title?: string; sub?: string; padded?: boolean }>(), { padded: true })
</script>

<style scoped>
.panel-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow-sm); overflow: hidden; }
.panel-card + .panel-card { margin-top: 16px; }
.panel-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 18px; border-bottom: 1px solid var(--border); gap: 12px; }
.panel-title { font-size: 14px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.panel-sub { font-size: 12px; color: var(--text-tertiary); font-weight: 400; }
.panel-actions { display: flex; gap: 8px; }
.panel-body.pad { padding: 16px 18px; }
</style>
