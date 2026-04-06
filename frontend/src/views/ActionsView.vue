<template>
  <section class="space-y-6">
    <LoadingState v-if="loading" message="正在加载处置记录..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="!items.length" title="没有处置记录" description="当前没有处置相关审计记录。" />
    <template v-else>
      <div class="table-shell">
        <table class="table-base">
          <thead>
            <tr>
              <th>处置人</th>
              <th>处置动作</th>
              <th>事件类型</th>
              <th>处置时间</th>
              <th>处置对象</th>
              <th>备注</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in items" :key="item.id">
              <td>{{ item.actor }}</td>
              <td>{{ item.message }}</td>
              <td>{{ eventTypeLabel(item.event_type) }}</td>
              <td>{{ formatDateTime(item.created_at) }}</td>
              <td>{{ item.resource_type }} / {{ item.resource_id }}</td>
              <td class="max-w-md text-slate-400">{{ JSON.stringify(item.details) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <BackToTopButton />
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { auditApi } from '@/api/modules/audit'
import BackToTopButton from '@/components/BackToTopButton.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import type { AuditLogItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const logs = ref<AuditLogItem[]>([])
const actionEventTypes = new Set([
  'email_actioned',
  'email_analyzed',
  'email_reanalyzed',
  'incident_created',
])

const items = computed(() =>
  logs.value.filter((item) => actionEventTypes.has(item.event_type)),
)

function eventTypeLabel(eventType: string): string {
  switch (eventType) {
    case 'email_actioned':
      return '邮件处置'
    case 'email_analyzed':
      return '邮件分析'
    case 'email_reanalyzed':
      return '重新分析'
    case 'incident_created':
      return '生成事件'
    case 'rule_created':
      return '创建规则'
    case 'rule_updated':
      return '更新规则'
    case 'user_report_created':
      return '用户上报'
    default:
      return eventType
  }
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    logs.value = await auditApi.list()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load actions'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
