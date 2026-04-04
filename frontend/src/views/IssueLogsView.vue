<template>
  <section class="space-y-6">
    <!-- <div>
      <p class="page-eyebrow">Issue Logs</p>
      <h1 class="page-title">问题日志</h1>
      <p class="page-subtitle">统一查看系统捕获到的问题，包括 LLM 降级原因、IMAP 测试失败和监听异常。</p>
    </div> -->

    <div class="panel">
      <div class="panel-body grid gap-4 md:grid-cols-3">
        <input v-model="filters.emailId" class="field" placeholder="按 email_id 过滤" />
        <input v-model="filters.component" class="field" placeholder="按 component 过滤" />
        <select v-model="filters.severity" class="field">
          <option value="">全部级别</option>
          <option value="info">info</option>
          <option value="warning">warning</option>
          <option value="error">error</option>
        </select>
      </div>
    </div>

    <LoadingState v-if="loading" message="正在加载问题日志..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="!filteredItems.length" title="没有匹配的问题日志" description="请调整过滤条件后重试。" />
    <div v-else class="table-shell">
      <table class="table-base">
        <thead>
          <tr>
            <th>时间</th>
            <th>级别</th>
            <th>组件</th>
            <th>问题</th>
            <th>详情</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filteredItems" :key="item.id">
            <td class="text-slate-500">{{ formatDateTime(item.created_at) }}</td>
            <td>
              <span
                class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em]"
                :class="severityClass(item.severity)"
              >
                {{ item.severity }}
              </span>
            </td>
            <td class="text-slate-600">{{ item.component }}</td>
            <td class="max-w-sm text-slate-900">{{ item.message }}</td>
            <td class="max-w-lg break-all text-slate-500">{{ JSON.stringify(item.details) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { issueLogsApi } from '@/api/modules/issueLogs'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import type { IssueLogItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const items = ref<IssueLogItem[]>([])
const filters = reactive({
  emailId: '',
  component: '',
  severity: '',
})

const filteredItems = computed(() =>
  items.value.filter((item) => {
    const emailId = filters.emailId.trim().toLowerCase()
    const component = filters.component.trim().toLowerCase()
    const detailsText = JSON.stringify(item.details).toLowerCase()
    const detailEmailId =
      typeof item.details.email_id === 'string'
        ? item.details.email_id.toLowerCase()
        : ''
    const matchesEmailId = !emailId || detailEmailId.includes(emailId) || detailsText.includes(emailId)
    const matchesComponent = !component || item.component.toLowerCase().includes(component)
    const matchesSeverity = !filters.severity || item.severity === filters.severity
    return matchesEmailId && matchesComponent && matchesSeverity
  }),
)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await issueLogsApi.list()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load issue logs'
  } finally {
    loading.value = false
  }
}

function severityClass(severity: string): string {
  if (severity === 'error') return 'bg-red-50 text-red-700'
  if (severity === 'warning') return 'bg-amber-50 text-amber-700'
  return 'bg-slate-100 text-slate-600'
}

onMounted(load)
</script>
