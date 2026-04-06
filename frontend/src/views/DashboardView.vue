<template>
  <section class="space-y-6">
    <LoadingState v-if="loading" message="正在加载仪表盘数据..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <template v-else>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="今日新邮件" :value="todayAnalyzed" subtitle="今天进入分析的邮件" tone="success" />
        <StatCard title="高风险邮件" :value="summary?.high_risk_emails ?? highRiskCount" subtitle="累计 high + critical" tone="warning" />
        <StatCard title="监听中的邮箱" :value="summary?.listening_mailboxes ?? 0" subtitle="个人邮箱监听状态" tone="neutral" />
        <StatCard title="邮箱异常" :value="summary?.mailbox_errors ?? 0" subtitle="需要检查连接" tone="danger" />
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.2fr,0.8fr]">
        <div class="panel overflow-hidden">
          <div class="panel-header">
            <div class="flex flex-wrap items-center gap-3">
              <h2 class="text-lg font-semibold text-slate-900">最近高风险邮件</h2>
              <div class="flex flex-wrap items-center gap-2">
                <button
                  v-for="option in alertWindowOptions"
                  :key="option.value"
                  class="btn-secondary"
                  type="button"
                  :class="selectedAlertWindow === option.value ? '!border-sky-300 !bg-sky-50 !text-sky-700' : ''"
                  @click="selectedAlertWindow = option.value"
                >
                  {{ option.label }}
                </button>
              </div>
            </div>
            <button class="btn-secondary" type="button" @click="toggleRecentAlerts">
              {{ showRecentAlerts ? '折叠' : '展开' }}
            </button>
          </div>
          <div v-if="showRecentAlerts" class="panel-body">
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
          <div class="panel-body grid gap-6 xl:grid-cols-2">
            <div class="rounded-[24px] border border-slate-200 bg-white p-5">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-rose-600">风险占比</p>
                  <p class="mt-2 text-sm text-slate-500">按当前邮件风险等级统计</p>
                </div>
                <div class="text-right">
                  <div class="text-2xl font-semibold tracking-[-0.04em] text-slate-950">{{ emails.length }}</div>
                  <div class="text-xs text-slate-500">总邮件</div>
                </div>
              </div>

              <div class="mt-5 flex min-h-[260px] items-center justify-center">
                <div class="relative h-56 w-56">
                  <svg viewBox="0 0 120 120" class="h-full w-full -rotate-90">
                    <circle cx="60" cy="60" r="42" fill="none" stroke="#e2e8f0" stroke-width="16" />
                    <circle
                      v-for="slice in riskChartSlices"
                      :key="slice.label"
                      cx="60"
                      cy="60"
                      r="42"
                      fill="none"
                      :stroke="slice.color"
                      stroke-width="16"
                      stroke-linecap="butt"
                      :stroke-dasharray="slice.dasharray"
                      :stroke-dashoffset="slice.dashoffset"
                    />
                  </svg>
                  <div class="absolute inset-0 flex flex-col items-center justify-center text-center">
                    <div class="text-3xl font-semibold tracking-[-0.05em] text-slate-950">{{ highRiskCount }}</div>
                    <div class="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">高风险合计</div>
                  </div>
                </div>
              </div>

              <div class="mt-5 space-y-3">
                <div
                  v-for="item in riskDistribution"
                  :key="item.label"
                  class="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3"
                >
                  <div class="flex items-center gap-3">
                    <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: item.color }"></span>
                    <span class="text-sm text-slate-700">{{ item.label }}</span>
                  </div>
                  <div class="text-right">
                    <div class="text-sm font-semibold text-slate-900">{{ item.count }}</div>
                    <div class="text-xs text-slate-500">{{ item.percentText }}</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-[24px] border border-slate-200 bg-white p-5">
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">平台数量</p>
                  <p class="mt-2 text-sm text-slate-500">不同邮箱平台的监听账户数量</p>
                </div>
                <div class="text-right">
                  <div class="text-2xl font-semibold tracking-[-0.04em] text-slate-950">{{ mailAccounts.length }}</div>
                  <div class="text-xs text-slate-500">监听邮箱</div>
                </div>
              </div>

              <template v-if="providerDistribution.length">
                <div class="mt-5 flex min-h-[260px] items-center justify-center">
                  <PlatformBarChart :data="providerDistribution" />
                </div>
                <div class="mt-5 space-y-3">
                  <div
                    v-for="item in providerSummaryRows"
                    :key="item.label"
                    class="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3"
                  >
                    <div class="flex items-center gap-3">
                      <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: item.color }"></span>
                      <span class="text-sm text-slate-700">{{ item.label }}</span>
                    </div>
                    <div class="text-right">
                      <div class="text-sm font-semibold text-slate-900">{{ item.value }}</div>
                      <div class="text-xs text-slate-500">{{ item.percentText }}</div>
                    </div>
                  </div>
                </div>
              </template>
              <div v-else class="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-sm text-slate-500">
                暂无监听邮箱数据。
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
import { mailAccountsApi } from '@/api/modules/mailAccounts'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import PlatformBarChart from '@/components/PlatformBarChart.vue'
import StatCard from '@/components/StatCard.vue'
import type { DashboardSummary, EmailListItem, MailAccountItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const summary = ref<DashboardSummary | null>(null)
const emails = ref<EmailListItem[]>([])
const mailAccounts = ref<MailAccountItem[]>([])
const showRecentAlerts = ref(true)
const selectedAlertWindow = ref<'7d' | '30d' | '90d' | 'all'>('30d')
const alertWindowOptions = [
  { label: '7天', value: '7d' as const },
  { label: '30天', value: '30d' as const },
  { label: '90天', value: '90d' as const },
  { label: '全部', value: 'all' as const },
]

const todayAnalyzed = computed(() => {
  const today = new Date().toDateString()
  return emails.value.filter((item) => new Date(item.created_at).toDateString() === today).length
})

const highRiskCount = computed(() => emails.value.filter((item) => ['high', 'critical'].includes(item.latest_risk_level ?? '')).length)
const recentAlerts = computed(() => {
  const now = Date.now()
  const days = selectedAlertWindow.value === '7d' ? 7 : selectedAlertWindow.value === '30d' ? 30 : selectedAlertWindow.value === '90d' ? 90 : null
  return [...emails.value]
    .filter((item) => ['high', 'critical'].includes(item.latest_risk_level ?? ''))
    .filter((item) => {
      if (days === null) return true
      return now - new Date(item.created_at).getTime() <= days * 24 * 60 * 60 * 1000
    })
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 6)
})

const riskDistribution = computed(() => {
  const palette: Record<string, string> = {
    critical: '#dc2626',
    high: '#f97316',
    medium: '#facc15',
    low: '#22c55e',
    unknown: '#64748b',
  }
  const counters = new Map<string, number>([
    ['critical', 0],
    ['high', 0],
    ['medium', 0],
    ['low', 0],
    ['unknown', 0],
  ])

  for (const email of emails.value) {
    const key = ['critical', 'high', 'medium', 'low'].includes(email.latest_risk_level ?? '') ? String(email.latest_risk_level) : 'unknown'
    counters.set(key, (counters.get(key) ?? 0) + 1)
  }

  const total = emails.value.length || 1
  return [
    { key: 'critical', label: 'Critical', color: palette.critical },
    { key: 'high', label: 'High', color: palette.high },
    { key: 'medium', label: 'Medium', color: palette.medium },
    { key: 'low', label: 'Low', color: palette.low },
    { key: 'unknown', label: '待定', color: palette.unknown },
  ]
    .map((item) => {
      const count = counters.get(item.key) ?? 0
      const percent = count / total
      return {
        ...item,
        count,
        percent,
        percentText: `${Math.round(percent * 100)}%`,
      }
    })
})

const riskChartSlices = computed(() => {
  const circumference = 2 * Math.PI * 42
  let offset = 0
  return riskDistribution.value.map((item) => {
    const length = item.percent * circumference
    const slice = {
      label: item.label,
      color: item.color,
      dasharray: `${length} ${circumference - length}`,
      dashoffset: `${-offset}`,
    }
    offset += length
    return slice
  })
})

const providerDistribution = computed(() => {
  const counts = new Map<string, number>([
    ['QQ', 0],
    ['Gmail', 0],
    ['Outlook', 0],
    ['163', 0],
    ['其他', 0],
  ])

  for (const account of mailAccounts.value) {
    const key =
      account.provider === 'qq'
        ? 'QQ'
        : account.provider === 'gmail'
          ? 'Gmail'
          : account.provider === 'outlook'
            ? 'Outlook'
            : account.provider === '163'
              ? '163'
              : '其他'
    counts.set(key, (counts.get(key) ?? 0) + 1)
  }

  return ['QQ', 'Gmail', 'Outlook', '163', '其他']
    .map((name) => ({ name, value: counts.get(name) ?? 0 }))
})

const providerSummaryRows = computed(() => {
  const colors: Record<string, string> = {
    QQ: '#7dd3fc',
    Gmail: '#38bdf8',
    Outlook: '#60a5fa',
    '163': '#93c5fd',
    其他: '#94a3b8',
  }
  const total = mailAccounts.value.length || 1
  return ['QQ', 'Gmail', 'Outlook', '163', '其他']
    .map((name) => ({ name, value: providerDistribution.value.find((item) => item.name === name)?.value ?? 0 }))
    .map((item) => ({
      label: item.name,
      value: item.value,
      color: colors[item.name],
      percentText: `${Math.round((item.value / total) * 100)}%`,
    }))
})

function toggleRecentAlerts(): void {
  showRecentAlerts.value = !showRecentAlerts.value
}

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
    const [summaryData, emailsData, mailAccountsData] = await Promise.all([dashboardApi.getSummary(), emailsApi.list(), mailAccountsApi.list()])
    summary.value = summaryData
    emails.value = emailsData
    mailAccounts.value = mailAccountsData
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load dashboard'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
