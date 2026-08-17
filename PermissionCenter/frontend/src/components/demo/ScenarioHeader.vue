<template>
  <div class="scenario-header">
    <div class="header-left">
      <div class="role-avatar" :class="{ active: role !== '—' }">
        {{ role === '—' ? '🌐' : role.slice(0, 1) }}
      </div>
      <div class="role-info">
        <div class="role-name">
          <template v-if="role !== '—'">{{ role }}</template>
          <template v-else>{{ scenarioTitle }}</template>
        </div>
        <div class="role-label" v-if="roleLabel !== role">{{ roleLabel }}</div>
      </div>
    </div>
    <div class="header-right">
      <span class="role-tag">{{ roleLabel }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  role: string
  roleLabel: string
  stepNum: number
  total: number
  scenarioTitle: string
}>()
</script>

<style scoped>
.scenario-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius) var(--radius) 0 0;
  border-bottom: none;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: var(--text-secondary);
  transition: all 0.3s;
  border: 2px solid var(--border);
}

.role-avatar.active {
  background: var(--brand-soft);
  border-color: var(--brand);
  color: var(--brand);
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.role-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
}

.role-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.role-tag {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
  padding: 4px 12px;
  border-radius: 20px;
}
</style>
