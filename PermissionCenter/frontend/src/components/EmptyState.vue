<template>
  <div class="empty-state"><slot>{{ text }}</slot></div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ text?: string }>(), { text: '暂无数据' })
</script>

<style scoped>
.empty-state { padding: 40px; text-align: center; color: var(--text-tertiary); font-size: 13px; }
</style>
