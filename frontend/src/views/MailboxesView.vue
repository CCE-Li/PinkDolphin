<template>
  <section class="space-y-6">
    <div class="flex justify-end">
      <button class="btn-primary" type="button" @click="openCreate">新增监听邮箱</button>
    </div>

    <LoadingState v-if="loading" message="正在加载邮箱监听状态..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <template v-else>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="监听邮箱数" :value="accounts.length" subtitle="你已接入的邮箱" tone="neutral" />
        <StatCard title="正在监听" :value="listeningCount" subtitle="后台持续检查新邮件" tone="success" />
        <StatCard title="连接异常" :value="errorCount" subtitle="建议先测试连接" tone="danger" />
        <div class="panel">
          <div class="panel-body">
            <button class="block w-full text-left" type="button" @click="toggleUidDetails">
              <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">累计同步 UID</p>
              <div class="mt-4 flex items-end justify-between gap-4">
                <div class="text-4xl font-semibold tracking-[-0.06em] text-slate-950">{{ syncedCount }}</div>
                <div class="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                  {{ showUidDetails ? '收起明细' : '增量同步进度' }}
                </div>
              </div>
            </button>

            <div v-if="showUidDetails" class="mt-4 space-y-3 border-t border-slate-100 pt-4">
              <div
                v-for="row in uidDetailRows"
                :key="row.id"
                class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3"
              >
                <div class="flex items-center justify-between gap-4">
                  <div class="min-w-0">
                    <div class="truncate text-sm font-semibold text-slate-900">{{ row.label }}</div>
                    <div class="mt-1 text-xs text-slate-500">{{ row.folder }}</div>
                  </div>
                  <div class="text-right text-sm text-slate-600">
                    <div>同步：{{ row.lastSynced }}</div>
                    <div class="mt-1">发现：{{ row.lastSeen }}</div>
                  </div>
                </div>
              </div>
              <div v-if="!uidDetailRows.length" class="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500">
                暂无可展示的 UID 明细。
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.1fr,0.9fr]">
        <div class="space-y-6">
          <div class="panel">
            <div class="panel-header">
              <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">监听状态概览</h2>
            </div>
            <div class="panel-body">
              <div class="grid gap-4 md:grid-cols-2">
                <div class="rounded-[24px] border border-slate-200 bg-white p-5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">状态分布</p>
                  <div class="mt-4 space-y-3">
                    <div v-for="row in statusRows" :key="row.status" class="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 px-4 py-3">
                      <div class="flex items-center gap-3">
                        <MailboxStatusBadge :status="row.status" />
                        <span class="text-sm text-slate-700">{{ row.label }}</span>
                      </div>
                      <span class="text-xl font-semibold tracking-[-0.04em] text-slate-950">{{ row.count }}</span>
                    </div>
                  </div>
                </div>

                <div class="rounded-[24px] border border-sky-100 bg-sky-50/70 p-5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">工作流程</p>
                  <div class="mt-4 grid gap-3">
                    <div v-for="step in flowSteps" :key="step.title" class="rounded-2xl border border-white/80 bg-white/80 px-4 py-3">
                      <div class="text-sm font-semibold tracking-[-0.02em] text-slate-950">{{ step.title }}</div>
                      <div class="mt-1 text-sm leading-7 text-slate-500">{{ step.description }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header">
              <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">监听邮箱列表</h2>
            </div>
            <div class="panel-body">
              <EmptyState v-if="!accounts.length" title="还没有监听邮箱" description="先绑定你的 QQ、Gmail、Outlook、163、阿里云邮箱或自定义 IMAP 邮箱，后面也可以继续新增多个邮箱。" />
              <div v-else class="space-y-4">
                <article
                  v-for="account in accounts"
                  :key="account.id"
                  class="rounded-[28px] border p-5 transition"
                  :class="selectedAccount?.id === account.id
                    ? 'border-sky-200 bg-sky-50/60'
                    : 'border-slate-200 bg-white hover:border-sky-100'"
                >
                  <div class="flex flex-wrap items-start justify-between gap-4">
                    <div class="min-w-0">
                      <div class="flex flex-wrap items-center gap-2">
                        <h3 class="text-lg font-semibold tracking-[-0.03em] text-slate-950">{{ account.display_name || account.email_address }}</h3>
                        <MailboxStatusBadge :status="account.status" />
                      </div>
                      <p class="mt-2 text-sm text-slate-500">{{ account.email_address }} · {{ account.provider }} · {{ account.mailbox_folder }}</p>
                      <p class="mt-1 text-sm text-slate-500">账户所有者：{{ account.owner_email }}</p>
                    </div>
                    <div class="grid min-w-[180px] gap-2 text-right text-sm text-slate-500">
                      <div>上次同步：{{ formatDateTime(account.last_sync_at) }}</div>
                      <div>已同步 UID：{{ account.last_synced_uid ?? '--' }}</div>
                      <div>已发现 UID：{{ account.last_seen_uid ?? '--' }}</div>
                    </div>
                  </div>

                  <div class="mt-4 grid gap-3 md:grid-cols-[1fr,auto]">
                    <div class="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                      <div>IMAP：{{ account.imap_host }}:{{ account.imap_port }}</div>
                      <div class="mt-1">监听间隔：{{ account.listen_interval_seconds }} 秒</div>
                      <div v-if="account.last_error" class="mt-2 text-red-600">最近错误：{{ account.last_error }}</div>
                    </div>
                    <div class="flex flex-wrap items-center justify-end gap-2">
                      <button class="btn-danger" type="button" :disabled="removingId === account.id" @click="removeAccount(account)">
                        {{ removingId === account.id ? '解绑中...' : '解绑邮箱' }}
                      </button>
                      <button class="btn-secondary" type="button" @click="selectAccount(account)">查看 / 编辑</button>
                      <button class="btn-secondary" type="button" :disabled="testingId === account.id" @click="runTest(account)">
                        {{ testingId === account.id ? '测试中...' : '测试连接' }}
                      </button>
                      <button class="btn-primary" type="button" :disabled="syncingId === account.id" @click="runSync(account)">
                        {{ syncingId === account.id ? '同步中...' : '立即同步' }}
                      </button>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="panel">
            <div class="panel-header">
              <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">连接状态面板</h2>
            </div>
            <div class="panel-body space-y-4">
              <div class="rounded-[24px] border border-sky-100 bg-sky-50/70 p-5">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">当前选中</p>
                <div v-if="selectedAccount" class="mt-3">
                  <div class="text-lg font-semibold tracking-[-0.03em] text-slate-950">{{ selectedAccount.display_name || selectedAccount.email_address }}</div>
                  <div class="mt-2 text-sm leading-7 text-slate-500">
                    {{ selectedAccount.imap_host }}:{{ selectedAccount.imap_port }} · {{ selectedAccount.imap_username }}
                  </div>
                </div>
                <div v-else class="mt-3 text-sm text-slate-500">尚未选中监听邮箱。</div>
              </div>

              <div class="grid gap-4 md:grid-cols-2">
                <div class="rounded-[24px] border border-slate-200 bg-white p-5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">测试结果</p>
                  <div class="mt-3 text-sm leading-7 text-slate-600">
                    <template v-if="testResult">
                      <div>状态：<span :class="testResult.ok ? 'text-sky-700' : 'text-red-600'">{{ testResult.ok ? '成功' : '失败' }}</span></div>
                      <div>消息：{{ testResult.message }}</div>
                      <div>最高 UID：{{ testResult.highest_uid ?? '--' }}</div>
                    </template>
                    <template v-else>还没有执行连接测试。</template>
                  </div>
                </div>

                <div class="rounded-[24px] border border-slate-200 bg-white p-5">
                  <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">同步结果</p>
                  <div class="mt-3 text-sm leading-7 text-slate-600">
                    <template v-if="syncResult">
                      <div>已同步数量：{{ syncResult.synced }}</div>
                      <div>队列任务数：{{ syncResult.queued }}</div>
                      <div>最高 UID：{{ syncResult.highest_uid ?? '--' }}</div>
                      <div>账户 ID：{{ syncResult.account_id }}</div>
                    </template>
                    <template v-else>还没有执行手动同步。</template>
                  </div>
                </div>
              </div>

              <div class="rounded-[24px] border border-slate-200 bg-white p-5">
                <p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">个人使用建议</p>
                <ul class="mt-3 space-y-2 pl-5 text-sm leading-7 text-slate-500">
                  <li>个人场景下，通常只需要先接入自己的主邮箱。</li>
                  <li>QQ、Gmail、163 等平台通常都需要先开启 IMAP，并使用授权码或应用密码。</li>
                  <li>如果你有工作邮箱、备用邮箱，也可以继续新增多个监听账户。</li>
                  <li>激活后系统会持续抓取增量新邮件并自动进入分析流水线。</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="isFormPanelOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm"
      @click.self="resetForm"
    >
      <div ref="formPanelRef" class="panel max-h-[90vh] w-full max-w-4xl overflow-y-auto">
        <div class="panel-header">
          <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">{{ editingAccount ? '编辑监听邮箱' : '新增监听邮箱' }}</h2>
        </div>
        <div class="panel-body">
          <MailAccountForm
            :initial-value="editingAccount"
            :submit-label="editingAccount ? '更新监听配置' : '创建监听配置'"
            :disabled="submitting"
            @submit="saveAccount"
            @cancel="resetForm"
          />
          <p v-if="formMessage" class="mt-4 text-sm text-sky-600">{{ formMessage }}</p>
          <p v-if="formError" class="mt-4 text-sm text-red-600">{{ formError }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { mailAccountsApi } from '@/api/modules/mailAccounts'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import MailAccountForm from '@/components/MailAccountForm.vue'
import MailboxStatusBadge from '@/components/MailboxStatusBadge.vue'
import StatCard from '@/components/StatCard.vue'
import type {
  MailAccountItem,
  MailAccountPayload,
  MailAccountSyncResult,
  MailAccountTestResult,
} from '@/types/api'
import { formatDateTime, formatNumber } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const accounts = ref<MailAccountItem[]>([])
const editingAccount = ref<MailAccountItem | null>(null)
const selectedAccount = ref<MailAccountItem | null>(null)
const submitting = ref(false)
const testingId = ref<string | null>(null)
const syncingId = ref<string | null>(null)
const removingId = ref<string | null>(null)
const formMessage = ref<string | null>(null)
const formError = ref<string | null>(null)
const testResult = ref<MailAccountTestResult | null>(null)
const syncResult = ref<MailAccountSyncResult | null>(null)
const formPanelRef = ref<HTMLElement | null>(null)
const showUidDetails = ref(false)
const isFormPanelOpen = ref(false)
let refreshTimer: number | null = null

const listeningCount = computed(() => accounts.value.filter((item) => item.status === 'listening').length)
const errorCount = computed(() => accounts.value.filter((item) => item.status === 'error').length)
const syncedCount = computed(() => accounts.value.reduce((sum, item) => sum + (item.last_synced_uid ?? 0), 0))
const uidDetailRows = computed(() =>
  accounts.value
    .filter((item) => item.last_synced_uid !== null || item.last_seen_uid !== null)
    .map((item) => ({
      id: item.id,
      label: item.display_name || item.email_address,
      folder: `${item.email_address} · ${item.mailbox_folder}`,
      lastSynced: formatNumber(item.last_synced_uid),
      lastSeen: formatNumber(item.last_seen_uid),
    })),
)
const statusRows = computed(() => [
  { status: 'listening', label: '监听中', count: accounts.value.filter((item) => item.status === 'listening').length },
  { status: 'idle', label: '空闲', count: accounts.value.filter((item) => item.status === 'idle').length },
  { status: 'error', label: '异常', count: accounts.value.filter((item) => item.status === 'error').length },
  { status: 'disabled', label: '停用', count: accounts.value.filter((item) => item.status === 'disabled').length },
])
const flowSteps = [
  { title: 'IMAP 持续监听', description: '后台保持对你的邮箱目录进行轮询和连接探测，尽快发现新邮件。' },
  { title: 'UID 增量同步', description: '只拉取上次已见 UID 之后的新邮件，减少重复处理。' },
  { title: '自动风险分析', description: '新邮件进入分析流水线后，自动生成风险等级、原因和建议动作。' },
]

function toggleUidDetails(): void {
  showUidDetails.value = !showUidDetails.value
}

async function load(options: { silent?: boolean } = {}): Promise<void> {
  if (!options.silent) {
    loading.value = true
    error.value = null
  }
  try {
    accounts.value = await mailAccountsApi.list()
    if (!selectedAccount.value && accounts.value.length) selectedAccount.value = accounts.value[0]
    if (selectedAccount.value) {
      selectedAccount.value = accounts.value.find((item) => item.id === selectedAccount.value?.id) ?? accounts.value[0] ?? null
    }
    if (editingAccount.value) {
      editingAccount.value = accounts.value.find((item) => item.id === editingAccount.value?.id) ?? null
    }
    if (!accounts.value.length) {
      selectedAccount.value = null
      editingAccount.value = null
    }
  } catch (err) {
    if (!options.silent) {
      error.value = err instanceof Error ? err.message : 'Failed to load mail accounts'
    }
  } finally {
    if (!options.silent) {
      loading.value = false
    }
  }
}

async function openCreate(): Promise<void> {
  isFormPanelOpen.value = true
  editingAccount.value = null
  selectedAccount.value = null
  formMessage.value = null
  formError.value = null
  testResult.value = null
  syncResult.value = null
  await nextTick()
  formPanelRef.value?.focus?.()
}

async function selectAccount(account: MailAccountItem): Promise<void> {
  isFormPanelOpen.value = true
  selectedAccount.value = account
  editingAccount.value = account
  formMessage.value = null
  formError.value = null
  await nextTick()
  formPanelRef.value?.focus?.()
}

function resetForm(): void {
  editingAccount.value = null
  isFormPanelOpen.value = false
}

async function saveAccount(payload: MailAccountPayload): Promise<void> {
  submitting.value = true
  formMessage.value = null
  formError.value = null
  try {
    if (editingAccount.value) {
      const updatePayload = { ...payload }
      if (!updatePayload.imap_password) delete updatePayload.imap_password
      await mailAccountsApi.update(editingAccount.value.id, updatePayload)
      formMessage.value = '监听配置已更新'
    } else {
      await mailAccountsApi.create(payload)
      formMessage.value = '监听邮箱已创建'
    }
    editingAccount.value = null
    isFormPanelOpen.value = false
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Save failed'
  } finally {
    submitting.value = false
  }
}

async function runTest(account: MailAccountItem): Promise<void> {
  selectedAccount.value = account
  testingId.value = account.id
  testResult.value = null
  formError.value = null
  try {
    testResult.value = await mailAccountsApi.test(account.id)
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Test failed'
  } finally {
    testingId.value = null
  }
}

async function runSync(account: MailAccountItem): Promise<void> {
  selectedAccount.value = account
  syncingId.value = account.id
  syncResult.value = null
  formError.value = null
  try {
    syncResult.value = await mailAccountsApi.sync(account.id)
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Sync failed'
  } finally {
    syncingId.value = null
  }
}

async function removeAccount(account: MailAccountItem): Promise<void> {
  const confirmed = window.confirm(`解绑 ${account.display_name || account.email_address} 后，会删除该邮箱配置和该邮箱已同步的所有邮件，继续吗？`)
  if (!confirmed) return

  removingId.value = account.id
  formMessage.value = null
  formError.value = null
  testResult.value = null
  syncResult.value = null
  try {
    const result = await mailAccountsApi.remove(account.id)
    if (selectedAccount.value?.id === account.id) {
      selectedAccount.value = null
    }
    if (editingAccount.value?.id === account.id) {
      editingAccount.value = null
    }
    isFormPanelOpen.value = false
    formMessage.value = `监听邮箱已解绑，并删除 ${result.deleted_email_count} 封关联邮件`
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Delete failed'
  } finally {
    removingId.value = null
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
