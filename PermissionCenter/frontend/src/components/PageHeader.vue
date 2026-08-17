<template>
  <header class="page-head">
    <div>
      <div class="page-title">{{ title }}</div>
      <div v-if="desc" class="page-desc">{{ desc }}</div>
    </div>
    <div v-if="$slots.actions" class="page-actions"><slot name="actions" /></div>
  </header>
</template>

<script setup lang="ts">
defineProps<{ title: string; desc?: string }>()
</script>

<style scoped>
.page-head { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 20px; gap: 16px; flex-wrap: wrap; }
.page-title { font-size: 22px; font-weight: 700; letter-spacing: -.01em; }
.page-desc { font-size: 13px; color: var(--text-secondary); margin-top: 2px; }
.page-actions { display: flex; gap: 8px; align-items: center; }
</style>
