<template>
  <section class="space-y-6">
    <div class="panel">
      <div class="panel-body grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <input v-model="filters.keyword" class="field xl:col-span-2" placeholder="搜索主题 / Message-ID" />
        <select v-model="filters.riskLevel" class="field">
          <option value="">全部风险等级</option>
          <option value="low">low</option>
          <option value="medium">medium</option>
          <option value="high">high</option>
          <option value="critical">critical</option>
        </select>
        <select v-model="filters.recommendedAction" class="field">
          <option value="">全部推荐动作</option>
          <option value="allow">allow</option>
          <option value="banner_warning">banner_warning</option>
          <option value="move_to_spam">move_to_spam</option>
          <option value="manual_review">manual_review</option>
          <option value="quarantine">quarantine</option>
        </select>
      </div>
    </div>
    <LoadingState v-if="loading" message="正在加载邮件列表..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState v-else-if="!paginatedEmails.length" title="没有匹配的邮件" description="请调整筛选条件后重试。" />
    <template v-else>
      <EmailTable :items="paginatedEmails" @select="openEmail" @delete="removeEmail" />
      <div class="flex items-center justify-between rounded-2xl border border-sky-100 bg-white/90 px-4 py-3">
        <div class="text-sm text-slate-500">共 {{ filteredEmails.length }} 条</div>
        <div class="flex gap-3">
          <button class="btn-secondary" type="button" :disabled="page === 1" @click="page--">上一页</button>
          <button class="btn-secondary" type="button" :disabled="page === totalPages" @click="page++">下一页</button>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { emailsApi } from '@/api/modules/emails'
import EmailTable from '@/components/EmailTable.vue'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import type { EmailListItem } from '@/types/api'

const router = useRouter()
const loading = ref(true)
const error = ref<string | null>(null)
const page = ref(1)
const pageSize = 10
const emails = ref<EmailListItem[]>([])
const filters = reactive({ keyword: '', riskLevel: '', recommendedAction: '' })
let refreshTimer: number | null = null

const filteredEmails = computed(() =>
  emails.value.filter((item) => {
    const keyword = filters.keyword.trim().toLowerCase()
    const matchesKeyword = !keyword || (item.subject ?? '').toLowerCase().includes(keyword) || (item.message_id ?? '').toLowerCase().includes(keyword)
    const matchesRisk = !filters.riskLevel || item.latest_risk_level === filters.riskLevel
    const matchesAction = !filters.recommendedAction || item.latest_recommended_action === filters.recommendedAction
    return matchesKeyword && matchesRisk && matchesAction
  }),
)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredEmails.value.length / pageSize)))
const paginatedEmails = computed(() => filteredEmails.value.slice((page.value - 1) * pageSize, page.value * pageSize))

watch(filteredEmails, () => {
  if (page.value > totalPages.value) page.value = totalPages.value
})

async function load(options: { silent?: boolean } = {}): Promise<void> {
  if (!options.silent) {
    loading.value = true
    error.value = null
  }
  try {
    emails.value = await emailsApi.list()
  } catch (err) {
    if (!options.silent) {
      error.value = err instanceof Error ? err.message : 'Failed to load emails'
    }
  } finally {
    if (!options.silent) {
      loading.value = false
    }
  }
}

function openEmail(id: string): void {
  void router.push(`/emails/${id}`)
}

async function removeEmail(email: EmailListItem): Promise<void> {
  const subject = email.subject || '(No Subject)'
  const confirmed = window.confirm(`确认删除这封邮件吗？\n\n主题：${subject}\n接收邮箱：${email.mailbox_email_address || '--'}`)
  if (!confirmed) return

  error.value = null
  try {
    await emailsApi.remove(email.id)
    emails.value = emails.value.filter((item) => item.id !== email.id)
    if (page.value > totalPages.value) page.value = totalPages.value
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to delete email'
  }
}

onMounted(async () => {
  await load()
  refreshTimer = window.setInterval(() => {
    void load({ silent: true })
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
})
</script>
