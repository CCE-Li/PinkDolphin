<template>
  <section class="space-y-6">
    <LoadingState v-if="loading" message="正在加载仪表盘数据..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <template v-else>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="今日新邮件" :value="todayAnalyzed" subtitle="今天进入分析的邮件" tone="success" />
        <StatCard title="高风险邮件" :value="summary?.high_risk_emails ?? highRiskCount" subtitle="high + critical" tone="warning" />
        <StatCard title="监听中的邮箱" :value="summary?.listening_mailboxes ?? 0" subtitle="个人邮箱监听状态" tone="neutral" />
        <StatCard title="邮箱异常" :value="summary?.mailbox_errors ?? 0" subtitle="需要检查连接" tone="danger" />
      </div>
      <div class="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <div class="panel">
          <div class="panel-header">
            <h2 class="text-lg font-semibold text-slate-900">最近高风险邮件</h2>
          </div>
          <div class="panel-body">
            <EmptyState v-if="!recentAlerts.length" title="暂无高风险邮件" description="当前没有 high 或 critical 级别的邮件。" />
            <div v-else class="space-y-3">
              <RouterLink
                v-for="email in recentAlerts"
                :key="email.id"
                :to="`/emails/${email.id}`"
                class="block rounded-2xl border p-4 transition"
                :class="alertCardClass(email.latest_risk_level)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="font-medium" :class="email.latest_risk_level === 'critical' ? 'text-red-950' : 'text-slate-900'">
                    {{ email.subject || '(No Subject)' }}
                  </div>
                  <RiskBadge :level="email.latest_risk_level" />
                </div>
                <div class="mt-2 text-sm" :class="email.latest_risk_level === 'critical' ? 'text-red-700' : 'text-slate-500'">
                  {{ formatDateTime(email.created_at) }} · Score {{ email.latest_score ?? '--' }}
                </div>
              </RouterLink>
            </div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-header">
            <h2 class="text-lg font-semibold text-slate-900">个人邮箱总览</h2>
          </div>
          <div class="panel-body space-y-4">
            <div class="rounded-2xl border border-sky-100 bg-sky-50/50 p-4">
              <div class="flex items-center justify-between gap-3">
                <span class="text-sm text-slate-600">已监听邮箱</span>
                <div class="text-lg font-semibold text-slate-900">{{ summary?.monitored_mailboxes ?? 0 }}</div>
              </div>
            </div>
            <div class="rounded-2xl border border-sky-100 bg-sky-50/50 p-4">
              <div class="flex items-center justify-between gap-3">
                <span class="text-sm text-slate-600">累计邮件</span>
                <div class="text-lg font-semibold text-slate-900">{{ summary?.total_emails ?? emails.length }}</div>
              </div>
            </div>
            <div class="rounded-2xl border border-sky-100 bg-sky-50/50 p-4">
              <div class="flex items-center justify-between gap-3">
                <span class="text-sm text-slate-600">Critical 邮件</span>
                <div class="text-lg font-semibold text-slate-900">{{ summary?.critical_emails ?? criticalCount }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { dashboardApi } from '@/api/modules/dashboard'
import { emailsApi } from '@/api/modules/emails'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import StatCard from '@/components/StatCard.vue'
import type { DashboardSummary, EmailListItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const summary = ref<DashboardSummary | null>(null)
const emails = ref<EmailListItem[]>([])

const todayAnalyzed = computed(() => {
  const today = new Date().toDateString()
  return emails.value.filter((item) => new Date(item.created_at).toDateString() === today).length
})
const highRiskCount = computed(() => emails.value.filter((item) => ['high', 'critical'].includes(item.latest_risk_level ?? '')).length)
const criticalCount = computed(() => emails.value.filter((item) => item.latest_risk_level === 'critical').length)
const recentAlerts = computed(() => [...emails.value].filter((item) => ['high', 'critical'].includes(item.latest_risk_level ?? '')).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 6))

function alertCardClass(level: string | null | undefined): string {
  if (level === 'critical') {
    return 'border-red-300 bg-red-50 shadow-sm hover:border-red-400 hover:bg-red-100/80'
  }
  if (level === 'high') {
    return 'border-orange-200 bg-orange-50 hover:border-orange-300 hover:bg-orange-100/70'
  }
  return 'border-sky-100 bg-sky-50/50 hover:border-sky-200'
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const [summaryData, emailsData] = await Promise.all([dashboardApi.getSummary(), emailsApi.list()])
    summary.value = summaryData
    emails.value = emailsData
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
