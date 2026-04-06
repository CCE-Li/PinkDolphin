<template>
  <section class="space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="page-eyebrow">Email Detail</p>
        <button class="btn-secondary mt-3" type="button" @click="goBack">
          返回上一页
        </button>
        <h1 class="text-2xl font-semibold tracking-[-0.04em] text-slate-950">标题: "{{ email?.subject || '(No Subject)' }}"</h1>
        <!-- <p class="mt-2 text-sm leading-7 text-slate-500">查看邮件基础信息、正文和原始 EML。</p> -->
        <div class="mt-3 space-y-1 text-sm text-slate-600">
          <div>Message ID: {{ email?.message_id || '--' }}</div>
          <div>发送时间: {{ formatDateTime(email?.send_time || null) }}</div>
        </div>
      </div>
      <div class="flex flex-wrap gap-2">
        <RiskBadge :level="email?.latest_risk_level" />
      </div>
    </div>

    <LoadingState v-if="loading" message="正在加载邮件详情..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="!email" title="没有邮件详情" description="当前邮件不存在或尚未加载完成。" />
    <template v-else>
      <div class="panel">
        <div class="panel-header">
          <h2 class="text-lg font-semibold text-slate-900">正文</h2>
          <div class="flex flex-wrap items-center gap-2">
            <button
              class="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50"
              type="button"
              @click="displayMode = displayMode === 'contained' ? 'expanded' : 'contained'"
            >
              模式切换: {{ displayMode === 'contained' ? '块内滚动' : '全部展开' }}
            </button>
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="rounded-full px-3 py-1 text-xs font-semibold transition"
              :class="activeTab === tab.key ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
              type="button"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>
        <div class="panel-body">
          <pre
            v-if="activeTab === 'text'"
            class="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm leading-7 text-slate-700"
            :class="contentClass"
          >{{ email.body_text || '--' }}</pre>

          <div
            v-else-if="activeTab === 'html'"
            class="rounded-2xl border border-slate-200 bg-white p-4 text-sm leading-7 text-slate-700"
            :class="contentClass"
          >
            <div class="email-html-render" v-html="wrappedHtmlBody" />
          </div>

          <pre
            v-else
            class="whitespace-pre-wrap rounded-2xl border border-slate-200 bg-slate-950 p-4 text-xs leading-6 text-slate-100"
            :class="contentClass"
          >{{ email.raw_email || '--' }}</pre>
        </div>
      </div>
      <BackToTopButton v-if="displayMode === 'expanded'" :threshold="320" />
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { emailsApi } from '@/api/modules/emails'
import BackToTopButton from '@/components/BackToTopButton.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import RiskBadge from '@/components/RiskBadge.vue'
import type { EmailDetail } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const error = ref<string | null>(null)
const email = ref<EmailDetail | null>(null)
const activeTab = ref<'text' | 'html' | 'raw'>('text')
const displayMode = ref<'contained' | 'expanded'>('contained')

const tabs = computed(() => {
  const items: Array<{ key: 'text' | 'html' | 'raw'; label: string }> = []
  if (email.value?.body_text) items.push({ key: 'text', label: '原文本' })
  if (email.value?.body_html) items.push({ key: 'html', label: 'HTML' })
  items.push({ key: 'raw', label: '原始 EML' })
  return items
})
const contentClass = computed(() =>
  displayMode.value === 'contained'
    ? 'max-h-[640px] overflow-auto'
    : '',
)
const wrappedHtmlBody = computed(() => buildEmailShell(sanitizeHtmlForDisplay(email.value?.body_html || '<p>--</p>')))

async function goBack(): Promise<void> {
  if (window.history.length > 1) {
    await router.back()
    return
  }
  await router.push('/emails')
}

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    email.value = await emailsApi.getById(String(route.params.id))
    activeTab.value = email.value.body_text ? 'text' : email.value.body_html ? 'html' : 'raw'
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load email detail'
  } finally {
    loading.value = false
  }
}

void load()

function sanitizeHtmlForDisplay(input: string): string {
  return input
    .replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, '')
    .replace(/\son\w+="[^"]*"/gi, '')
    .replace(/\son\w+='[^']*'/gi, '')
    .replace(/javascript:/gi, '')
}

function buildEmailShell(content: string): string {
  return `
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;border-collapse:collapse;border-spacing:0;background:#f3f6fb;margin:0;padding:0;">
      <tr>
        <td align="center" style="padding:32px 20px;">
          <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="width:100%;max-width:640px;border-collapse:collapse;border-spacing:0;margin:0 auto;">
            <tr>
              <td style="padding:0;">
                ${content}
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  `.trim()
}
</script>

<style scoped>
.email-html-render :deep(table[role='presentation']) {
  border-collapse: collapse;
}

.email-html-render :deep(td),
.email-html-render :deep(th) {
  vertical-align: top;
}

.email-html-render :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
}

.email-html-render :deep(table) {
  max-width: 100%;
}

.email-html-render :deep(a) {
  color: rgb(3 105 161);
  text-decoration: underline;
}

.email-html-render :deep(pre) {
  white-space: pre-wrap;
}

.email-html-render :deep(body),
.email-html-render :deep(.email-container),
.email-html-render :deep(.container),
.email-html-render :deep(.wrapper),
.email-html-render :deep(.card),
.email-html-render :deep(.content) {
  margin-left: auto !important;
  margin-right: auto !important;
}
</style>
