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
                    <button class="btn-danger" type="button" :disabled="removingId === selectedAccount.id" @click="openRemoveDialog(selectedAccount)">
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

    <div
      v-if="pendingRemovalAccount"
      class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm"
    >
      <div class="panel w-full max-w-xl">
        <div class="panel-header">
          <div>
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">解绑邮箱账户</h2>
            <p class="mt-2 text-sm text-slate-500">选择解绑范围。</p>
          </div>
        </div>
        <div class="panel-body space-y-4">
          <div class="rounded-[22px] border border-slate-200 bg-slate-50 px-4 py-4">
            <div class="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">当前账户</div>
            <div class="mt-2 text-base font-semibold tracking-[-0.02em] text-slate-950">
              {{ pendingRemovalAccount.display_name || pendingRemovalAccount.email_address }}
            </div>
            <div class="mt-1 text-sm text-slate-500">
              {{ pendingRemovalAccount.email_address }} · {{ pendingRemovalAccount.provider_label }}
            </div>
          </div>
          <div class="grid gap-3">
            <button
              class="group rounded-[24px] border border-slate-200 bg-white px-5 py-4 text-left transition hover:border-sky-200 hover:bg-sky-50/40 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="removingId === pendingRemovalAccount.id"
              @click="removeAccount(pendingRemovalAccount, false)"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <div class="text-base font-semibold tracking-[-0.02em] text-slate-950">仅删本地</div>
                  <div class="mt-1 text-sm text-slate-500">移除账户配置、本地邮件与分析记录。</div>
                </div>
                <div class="rounded-full bg-sky-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-sky-700">
                  推荐
                </div>
              </div>
              <div class="mt-3 text-xs uppercase tracking-[0.16em] text-slate-400">
                真实邮箱不受影响
              </div>
            </button>
            <button
              class="group rounded-[24px] border border-red-200 bg-white px-5 py-4 text-left transition hover:border-red-300 hover:bg-red-50/40 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="removingId === pendingRemovalAccount.id"
              @click="openRemoteDeleteConfirm(pendingRemovalAccount)"
            >
              <div class="flex items-start justify-between gap-4">
                <div>
                  <div class="text-base font-semibold tracking-[-0.02em] text-red-700">删除远端</div>
                  <div class="mt-1 text-sm text-slate-500">同时删除真实邮箱中的对应邮件。</div>
                </div>
                <div class="rounded-full bg-red-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-red-700">
                  高风险
                </div>
              </div>
              <div class="mt-3 text-xs uppercase tracking-[0.16em] text-red-500">
                不可恢复
              </div>
            </button>
          </div>
          <div class="flex justify-end">
            <button class="btn-secondary" type="button" :disabled="Boolean(removingId)" @click="closeRemoveDialog">关闭</button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="remoteDeleteConfirmAccount"
      class="fixed inset-0 z-[60] flex items-center justify-center bg-slate-950/45 px-4 py-6 backdrop-blur-sm"
    >
      <div class="panel w-full max-w-xl">
        <div class="panel-header">
          <div>
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-red-700">高风险确认</h2>
            <p class="mt-2 text-sm text-slate-500">确认后将尝试删除真实邮箱中的对应邮件。</p>
          </div>
        </div>
        <div class="panel-body space-y-4">
          <div class="rounded-[22px] border border-red-200 bg-red-50/70 px-4 py-4 text-sm leading-7 text-slate-700">
            <div class="font-semibold text-red-700">
              {{ remoteDeleteConfirmAccount.display_name || remoteDeleteConfirmAccount.email_address }}
            </div>
            <div class="mt-1">
              将删除本系统中已同步的邮件，并尝试同步删除真实邮箱中的对应邮件。该操作不可恢复。
            </div>
          </div>
          <label class="flex items-start gap-3 rounded-[20px] border border-slate-200 bg-white px-4 py-4 text-sm leading-7 text-slate-700">
            <input v-model="remoteDeleteRiskAcknowledged" type="checkbox" class="mt-1" />
            <span>我已了解这会影响真实邮箱，且无法恢复。</span>
          </label>
          <div class="flex items-center justify-between gap-4">
            <div class="rounded-full bg-slate-100 px-3 py-2 text-sm text-slate-500">
              <template v-if="remoteDeleteCooldown > 0">{{ remoteDeleteCooldown }}s 后可确认</template>
              <template v-else>已解锁确认</template>
            </div>
            <div class="flex gap-3">
              <button class="btn-secondary" type="button" :disabled="Boolean(removingId)" @click="closeRemoteDeleteConfirm">返回</button>
              <button
                class="btn-danger"
                type="button"
                :disabled="Boolean(removingId) || !remoteDeleteRiskAcknowledged || remoteDeleteCooldown > 0"
                @click="confirmRemoteDelete"
              >
                {{ removingId === remoteDeleteConfirmAccount.id ? '删除中...' : '确认远端删除' }}
              </button>
            </div>
          </div>
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
const pendingRemovalAccount = ref<MailAccountItem | null>(null)
const remoteDeleteConfirmAccount = ref<MailAccountItem | null>(null)
const remoteDeleteRiskAcknowledged = ref(false)
const remoteDeleteCooldown = ref(0)
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
let remoteDeleteCooldownTimer: number | null = null

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

function openRemoveDialog(account: MailAccountItem): void {
  pendingRemovalAccount.value = account
  formMessage.value = null
  formError.value = null
}

function closeRemoveDialog(): void {
  if (removingId.value) return
  pendingRemovalAccount.value = null
}

function openRemoteDeleteConfirm(account: MailAccountItem): void {
  remoteDeleteConfirmAccount.value = account
  remoteDeleteRiskAcknowledged.value = false
  remoteDeleteCooldown.value = 3
  if (remoteDeleteCooldownTimer !== null) {
    window.clearInterval(remoteDeleteCooldownTimer)
  }
  remoteDeleteCooldownTimer = window.setInterval(() => {
    if (remoteDeleteCooldown.value <= 1) {
      remoteDeleteCooldown.value = 0
      if (remoteDeleteCooldownTimer !== null) {
        window.clearInterval(remoteDeleteCooldownTimer)
        remoteDeleteCooldownTimer = null
      }
      return
    }
    remoteDeleteCooldown.value -= 1
  }, 1000)
}

function closeRemoteDeleteConfirmInternal(force = false): void {
  if (removingId.value && !force) return
  remoteDeleteConfirmAccount.value = null
  remoteDeleteRiskAcknowledged.value = false
  remoteDeleteCooldown.value = 0
  if (remoteDeleteCooldownTimer !== null) {
    window.clearInterval(remoteDeleteCooldownTimer)
    remoteDeleteCooldownTimer = null
  }
}

function closeRemoteDeleteConfirm(): void {
  closeRemoteDeleteConfirmInternal(false)
}

async function confirmRemoteDelete(): Promise<void> {
  if (!remoteDeleteConfirmAccount.value) return
  await removeAccount(remoteDeleteConfirmAccount.value, true)
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

async function removeAccount(account: MailAccountItem, deleteRemote: boolean): Promise<void> {
  removingId.value = account.id
  formMessage.value = null
  formError.value = null
  testResult.value = null
  syncResult.value = null
  try {
    const result = await mailAccountsApi.remove(account.id, { deleteRemote })
    if (selectedAccount.value?.id === account.id) {
      selectedAccount.value = null
    }
    if (editingAccount.value?.id === account.id) {
      editingAccount.value = null
    }
    isFormPanelOpen.value = false
    pendingRemovalAccount.value = null
    closeRemoteDeleteConfirmInternal(true)
    formMessage.value = deleteRemote
      ? `邮箱账户已解绑，并删除本地与远端共 ${result.deleted_email_count} 封关联邮件`
      : `邮箱账户已解绑，并删除本地 ${result.deleted_email_count} 封关联邮件`
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
  if (remoteDeleteCooldownTimer !== null) {
    window.clearInterval(remoteDeleteCooldownTimer)
  }
})
</script>
