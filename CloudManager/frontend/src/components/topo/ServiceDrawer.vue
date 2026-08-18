<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  open: boolean
  service: any
  instances: any[]
  port: string
  deps: { group: string; name: string; relation_type: string; strength: string; port: string }[]
}>()

const emit = defineEmits<{
  (e: 'update:open', v: boolean): void
  (e: 'instance-click', id: number): void
}>()

const groups = computed(() => [
  { key: 'down', label: '⬇️ 下游依赖（本服务依赖）', items: props.deps.filter((d) => d.group === 'down') },
  { key: 'up', label: '⬆️ 上游调用（依赖本服务）', items: props.deps.filter((d) => d.group === 'up') },
  { key: 'comm', label: '⇄ 相互通信', items: props.deps.filter((d) => d.group === 'comm') },
])
</script>

<template>
  <a-drawer :open="open" :width="540" title="🔍 服务详情" @update:open="emit('update:open', $event)">
    <template v-if="service">
      <a-descriptions :column="2" bordered size="small">
        <a-descriptions-item label="服务名称">{{ service.name }}</a-descriptions-item>
        <a-descriptions-item label="类型">{{ service.service_type_display }}</a-descriptions-item>
        <a-descriptions-item label="部署方式">{{ service.deploy_type_display }}</a-descriptions-item>
        <a-descriptions-item label="状态">{{ service.status }}</a-descriptions-item>
        <a-descriptions-item label="端口">{{ port }}</a-descriptions-item>
        <a-descriptions-item label="实例数">{{ instances.length }}</a-descriptions-item>
        <a-descriptions-item label="所属环境" :span="2">{{ service.environment_name || '-' }}</a-descriptions-item>
      </a-descriptions>

      <p style="margin-top: 16px; font-weight: 600">实例清单（点击查看实例详情）</p>
      <a-table
        :columns="[
          { title: '实例', dataIndex: 'name' },
          { title: '规格', dataIndex: 'spec' },
          { title: '状态', dataIndex: 'status' },
          { title: '操作', key: 'action' },
        ]"
        :data-source="instances"
        row-key="id"
        size="small"
        :pagination="false"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-button size="small" type="link" @click="emit('instance-click', record.id)">查看详情</a-button>
          </template>
        </template>
      </a-table>

      <p style="margin-top: 16px; font-weight: 600">依赖资源（上下游标记）</p>
      <template v-for="g in groups" :key="g.key">
        <a-divider style="margin: 8px 0">{{ g.label }}</a-divider>
        <a-table
          v-if="g.items.length"
          :columns="[
            { title: '对象', dataIndex: 'name' },
            { title: '关系', dataIndex: 'relation_type' },
            { title: '强度', dataIndex: 'strength' },
            { title: '端口', dataIndex: 'port' },
          ]"
          :data-source="g.items"
          row-key="name"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'strength'">
              <a-tag :color="record.strength === 'hard' ? 'purple' : 'default'">{{ record.strength === 'hard' ? '强制' : '软' }}</a-tag>
            </template>
          </template>
        </a-table>
        <a-empty v-else :description="`暂无${g.label}`" :image-style="{ height: '36px' }" />
      </template>
    </template>
  </a-drawer>
</template>
