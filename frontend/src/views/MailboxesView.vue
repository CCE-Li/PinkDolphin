<template>
  <section class="space-y-6">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-2xl font-semibold tracking-[-0.04em] text-slate-950">邮箱客户端</h1>
        <p class="mt-2 text-sm text-slate-500">
          统一接入 Gmail、Outlook、QQ、163、阿里云或自定义 IMAP，把账户、文件夹和同步状态放在同一视图里管理。
        </p>
      </div>
      <button class="btn-primary" type="button" @click="openCreate">新增 IMAP 邮箱</button>
    </div>

    <LoadingState v-if="loading" message="正在加载邮箱账户..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <template v-else>
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard title="邮箱账户" :value="accounts.length" subtitle="已接入客户端" tone="neutral" />
        <StatCard title="监听中" :value="listeningCount" subtitle="后台持续同步" tone="success" />
        <StatCard title="连接异常" :value="errorCount" subtitle="建议先测试连接" tone="danger" />
        <StatCard title="主文件夹同步进度" :value="syncedCount" subtitle="客户端主目录累计处理数" tone="neutral" />
      </div>

      <div class="grid gap-6 xl:grid-cols-[320px,1fr]">
        <aside class="panel">
          <div class="panel-header">
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">账户列表</h2>
          </div>
          <div class="panel-body">
            <EmptyState
              v-if="!accounts.length"
              title="还没有邮箱账户"
              description="先接入 Gmail、Outlook 或其它 IMAP 邮箱，后面可继续追加多个账户。"
            />
            <div v-else class="space-y-3">
              <button
                v-for="account in accounts"
                :key="account.id"
                class="w-full rounded-[24px] border px-4 py-4 text-left transition"
                :class="selectedAccount?.id === account.id
                  ? 'border-sky-200 bg-sky-50/70'
                  : 'border-slate-200 bg-white hover:border-sky-100'"
                type="button"
                @click="selectAccount(account)"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <div class="truncate text-base font-semibold tracking-[-0.02em] text-slate-950">
                      {{ account.display_name || account.email_address }}
                    </div>
                    <div class="mt-1 truncate text-sm text-slate-500">{{ account.provider_label }}</div>
                    <div class="mt-2 truncate text-xs uppercase tracking-[0.18em] text-sky-600">{{ account.mailbox_folder }}</div>
                  </div>
                  <MailboxStatusBadge :status="account.status" />
                </div>
                <div class="mt-4 grid gap-1 text-xs text-slate-500">
                  <div>发现进度：{{ formatNumber(account.last_seen_uid) }}</div>
                  <div>同步进度：{{ formatNumber(account.last_synced_uid) }}</div>
                </div>
              </button>
            </div>
          </div>
        </aside>

        <div class="space-y-6">
          <EmptyState
            v-if="!selectedAccount"
            title="选择一个邮箱账户"
            description="左侧会像邮箱客户端的账号栏一样展示你已经接入的账户。"
          />

          <template v-else>
            <div class="panel">
              <div class="panel-body grid gap-5 lg:grid-cols-[1.4fr,0.9fr]">
                <div>
                  <div class="flex flex-wrap items-center gap-3">
                    <h2 class="text-2xl font-semibold tracking-[-0.04em] text-slate-950">
                      {{ selectedAccount.display_name || selectedAccount.email_address }}
                    </h2>
                    <MailboxStatusBadge :status="selectedAccount.status" />
                  </div>
                  <div class="mt-3 text-sm leading-7 text-slate-500">
                    {{ selectedAccount.email_address }} · {{ selectedAccount.provider_label }} ·
                    {{ selectedAccount.imap_host }}:{{ selectedAccount.imap_port }}
                  </div>
                  <!-- <div class="mt-5 rounded-[24px] border border-sky-100 bg-sky-50/70 px-5 py-4 text-sm leading-7 text-slate-600">
                    <div class="font-semibold text-slate-900">认证建议</div>
                    <div class="mt-1">{{ selectedAccount.auth_hint }}</div>
                    <div class="mt-2">
                      {{ selectedAccount.supports_app_password ? '支持应用密码 / 授权码场景' : '按标准 IMAP 凭据接入' }}
                    </div>
                  </div> -->
                </div>

                  <div class="grid gap-3">
                    <div class="rounded-[24px] border border-slate-200 bg-white px-5 py-4 text-sm text-slate-600">
                      <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-600">连接信息</div>
                      <div class="mt-3">用户名：{{ selectedAccount.imap_username }}</div>
                      <div class="mt-1">同步模式：{{ selectedAccount.sync_mode }}</div>
                      <div class="mt-1">监听方式：{{ selectedAccount.listener_mode === 'idle_fallback' ? 'IMAP IDLE + 兜底' : '纯轮询' }}</div>
                      <div class="mt-1">轮询间隔：{{ selectedAccount.listen_interval_seconds }} 秒</div>
                      <div class="mt-1">上次同步：{{ formatDateTime(selectedAccount.last_sync_at) }}</div>
                      <div v-if="selectedAccount.last_error" class="mt-2 text-red-600">最近错误：{{ selectedAccount.last_error }}</div>
                    </div>

                  <div class="flex flex-wrap gap-2">
                    <button
                      v-if="selectedAccount.sync_mode !== 'graph'"
                      class="btn-secondary"
                      type="button"
                      @click="openEdit(selectedAccount)"
                    >
                      编辑账户
                    </button>
                    <button
                      v-else
                      class="btn-secondary"
                      type="button"
                      :disabled="outlookConnecting"
                      @click="reconnectOutlook"
                    >
                      {{ outlookConnecting ? '跳转中...' : '重新授权 Outlook' }}
                    </button>
                    <button class="btn-secondary" type="button" :disabled="testingId === selectedAccount.id" @click="runTest(selectedAccount)">
                      {{ testingId === selectedAccount.id ? '测试中...' : '测试连接' }}
                    </button>
                    <button class="btn-primary" type="button" :disabled="syncingId === selectedAccount.id" @click="runSync(selectedAccount)">
                      {{ syncingId === selectedAccount.id ? '同步中...' : '立即同步' }}
                    </button>
                    <button class="btn-danger" type="button" :disabled="removingId === selectedAccount.id" @click="removeAccount(selectedAccount)">
                      {{ removingId === selectedAccount.id ? '解绑中...' : '解绑账户' }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid gap-6 lg:grid-cols-[0.95fr,1.05fr]">
              <div class="panel">
                <div class="panel-header">
                  <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">文件夹导航</h2>
                  <button class="btn-secondary" type="button" @click="toggleFolderNav">
                    {{ foldersCollapsed ? '展开' : '收起' }}
                  </button>
                </div>
                <div v-if="!foldersCollapsed" class="panel-body">
                  <div class="space-y-3">
                    <div
                      v-for="folder in selectedFolders"
                      :key="folder.name"
                      class="rounded-[24px] border px-4 py-4"
                      :class="folder.is_primary ? 'border-sky-200 bg-sky-50/60' : 'border-slate-200 bg-white'"
                    >
                      <div class="flex items-center justify-between gap-3">
                        <div>
                          <div class="text-sm font-semibold text-slate-950">{{ folder.label }}</div>
                          <div class="mt-1 text-xs text-slate-500">{{ folder.name }}</div>
                        </div>
                        <div class="rounded-full px-3 py-1 text-xs font-semibold"
                          :class="folder.is_primary ? 'bg-sky-100 text-sky-700' : 'bg-slate-100 text-slate-600'">
                          {{ folder.is_primary ? '当前同步目录' : '建议目录' }}
                        </div>
                      </div>
                      <div class="mt-4 grid gap-1 text-sm text-slate-500">
                        <div>发现进度：{{ formatNumber(folder.last_seen_uid) }}</div>
                        <div>同步进度：{{ formatNumber(folder.last_synced_uid) }}</div>
                        <div>最后同步：{{ formatDateTime(folder.last_sync_at) }}</div>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else class="px-6 pb-6 text-sm text-slate-500">
                  已折叠，点击右上角“展开”查看 {{ selectedFolders.length }} 个文件夹状态。
                </div>
              </div>

              <div class="space-y-6">
                <div class="panel">
                  <div class="panel-header">
                    <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">客户端工作流</h2>
                  </div>
                  <div class="panel-body grid gap-3">
                    <div v-for="step in flowSteps" :key="step.title" class="rounded-[24px] border border-slate-200 bg-white px-5 py-4">
                      <div class="text-sm font-semibold tracking-[-0.02em] text-slate-950">{{ step.title }}</div>
                      <div class="mt-2 text-sm leading-7 text-slate-500">{{ step.description }}</div>
                    </div>
                  </div>
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
                        <div>最高 UID / 进度：{{ syncResult.highest_uid ?? '--' }}</div>
                        <div>账户 ID：{{ syncResult.account_id }}</div>
                      </template>
                      <template v-else>还没有执行手动同步。</template>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <div
      v-if="isFormPanelOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm"
    >
      <div ref="formPanelRef" class="panel max-h-[90vh] w-full max-w-4xl overflow-y-auto">
        <div class="panel-header">
          <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">{{ editingAccount ? '编辑邮箱账户' : '新增邮箱账户' }}</h2>
        </div>
        <div class="panel-body">
          <MailAccountForm
            :initial-value="editingAccount"
            :submit-label="editingAccount ? '更新邮箱配置' : '创建邮箱配置'"
            :disabled="submitting"
            @submit="saveAccount"
            @cancel="resetForm"
            @open-config="openConfigManagement"
            @connect-outlook="connectOutlook"
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
import { useRoute, useRouter } from 'vue-router'

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
  OutlookOAuthStartPayload,
} from '@/types/api'
import { formatDateTime, formatNumber } from '@/utils/format'

const route = useRoute()
const router = useRouter()
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
const isFormPanelOpen = ref(false)
const outlookConnecting = ref(false)
const foldersCollapsed = ref(true)
let refreshTimer: number | null = null

const listeningCount = computed(() => accounts.value.filter((item) => item.status === 'listening').length)
const errorCount = computed(() => accounts.value.filter((item) => item.status === 'error').length)
const syncedCount = computed(() => accounts.value.reduce((sum, item) => sum + (item.last_synced_uid ?? 0), 0))
const selectedFolders = computed(() => selectedAccount.value?.folders ?? [])
const flowSteps = [
  { title: 'Provider Preset', description: '统一由后端维护 Gmail、Outlook 和其它邮箱的 IMAP 主机、认证提示和建议文件夹。' },
  { title: 'Folder Cursor', description: '每个邮箱账户保留主文件夹同步进度，并按客户端方式展示文件夹状态。' },
  { title: 'Sync Pipeline', description: '增量拉取新邮件后进入分析队列，后续风险评分、动作建议和日志都沿用现有链路。' },
]

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
    if (editingAccount.value && !isFormPanelOpen.value) {
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
  formMessage.value = null
  formError.value = null
  testResult.value = null
  syncResult.value = null
  await nextTick()
  formPanelRef.value?.focus?.()
}

async function connectOutlook(payload?: OutlookOAuthStartPayload): Promise<void> {
  outlookConnecting.value = true
  formError.value = null
  try {
    const response = await mailAccountsApi.startOutlookOAuth(
      payload ?? {
        is_active: true,
        mailbox_folder: 'INBOX',
        listen_interval_seconds: 5,
        listener_mode: 'polling',
      },
    )
    window.location.href = response.authorization_url
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Failed to start Outlook OAuth'
    outlookConnecting.value = false
  }
}

async function reconnectOutlook(): Promise<void> {
  const account = selectedAccount.value
  await connectOutlook(
    account
      ? {
          owner_email: account.owner_email,
          display_name: account.display_name,
          mailbox_folder: account.mailbox_folder,
          is_active: account.is_active,
          listen_interval_seconds: account.listen_interval_seconds,
          listener_mode: account.listener_mode,
        }
      : undefined,
  )
}

async function selectAccount(account: MailAccountItem): Promise<void> {
  selectedAccount.value = account
  formMessage.value = null
  formError.value = null
}

async function openEdit(account: MailAccountItem): Promise<void> {
  selectedAccount.value = account
  editingAccount.value = account
  isFormPanelOpen.value = true
  formMessage.value = null
  formError.value = null
  await nextTick()
  formPanelRef.value?.focus?.()
}

function resetForm(): void {
  editingAccount.value = null
  isFormPanelOpen.value = false
}

function openConfigManagement(): void {
  isFormPanelOpen.value = false
  void router.push('/config-management')
}

function toggleFolderNav(): void {
  foldersCollapsed.value = !foldersCollapsed.value
}

async function saveAccount(payload: MailAccountPayload): Promise<void> {
  submitting.value = true
  formMessage.value = null
  formError.value = null
  try {
    let savedAccount: MailAccountItem
    if (editingAccount.value) {
      const updatePayload = { ...payload }
      if (!updatePayload.imap_password) delete updatePayload.imap_password
      savedAccount = await mailAccountsApi.update(editingAccount.value.id, updatePayload)
      formMessage.value = '邮箱配置已更新'
    } else {
      savedAccount = await mailAccountsApi.create(payload)
      formMessage.value = '邮箱账户已创建'
    }
    if (payload.listener_mode === 'idle_fallback' && savedAccount.listener_mode !== 'idle_fallback') {
      formMessage.value = `${formMessage.value}；当前后端还不支持保存“IMAP IDLE + 兜底”，已按纯轮询处理`
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
    formMessage.value = `邮箱账户已解绑，并删除 ${result.deleted_email_count} 封关联邮件`
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Delete failed'
  } finally {
    removingId.value = null
  }
}

onMounted(async () => {
  const oauth = route.query.oauth
  const status = route.query.status
  const message = route.query.message
  if (oauth === 'outlook' && typeof status === 'string' && typeof message === 'string') {
    if (status === 'success') {
      formMessage.value = message
    } else {
      formError.value = message
    }
    await router.replace({ path: '/mailboxes' })
  }
  await load()
  refreshTimer = window.setInterval(() => {
    if (!isFormPanelOpen.value) {
      void load({ silent: true })
    }
  }, 5000)
})

onBeforeUnmount(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer)
  }
})
</script>
