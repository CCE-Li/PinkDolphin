<template>
  <form class="grid gap-4" @submit.prevent="submit">
    <div class="grid gap-4 md:grid-cols-2">
      <div>
        <label class="mb-2 block text-sm font-medium text-slate-600">本人邮箱</label>
        <input v-model="form.owner_email" class="field" placeholder="留空时默认等于被监听邮箱" :disabled="disabled" />
      </div>
      <div>
        <label class="mb-2 block text-sm font-medium text-slate-600">被监听邮箱</label>
        <input v-model="form.email_address" class="field" placeholder="your@example.com" :disabled="disabled" required />
      </div>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <div>
        <label class="mb-2 block text-sm font-medium text-slate-600">展示名称</label>
        <input v-model="form.display_name" class="field" placeholder="主邮箱 / 工作邮箱 / 备用邮箱" :disabled="disabled" />
      </div>
      <div>
        <label class="mb-2 block text-sm font-medium text-slate-600">邮箱提供商</label>
        <select v-model="form.provider" class="field" :disabled="disabled">
          <option v-for="provider in providerOptions" :key="provider.value" :value="provider.value">
            {{ provider.label }}
          </option>
        </select>
      </div>
    </div>

    <div class="rounded-[24px] border border-sky-100 bg-sky-50/70 px-5 py-4 text-sm leading-7 text-slate-600">
      <div class="font-semibold text-slate-900">{{ currentProviderPreset.label }}</div>
      <div class="mt-1">{{ currentProviderPreset.auth_hint }}</div>
      <div class="mt-2">建议文件夹：{{ currentProviderPreset.suggested_folders.join(' / ') }}</div>
    </div>

    <div
      v-if="form.provider === 'outlook'"
      class="rounded-[28px] border border-sky-100 bg-sky-50/70 px-5 py-5 text-sm leading-7 text-slate-600"
    >
      <div class="flex flex-wrap items-start justify-between gap-4">
        <div class="max-w-2xl">
          <div class="font-semibold text-slate-900">Outlook / Microsoft 365</div>
          <div class="mt-1">Outlook 使用 Microsoft Graph OAuth2，不再走 IMAP 密码登录。</div>
          <!-- <div class="mt-2">
            先在“配置管理”中填写 `MICROSOFT_CLIENT_ID`、`MICROSOFT_CLIENT_SECRET`、`BACKEND_PUBLIC_URL`、`FRONTEND_APP_URL`，再点击“连接 Outlook (Graph)”。
          </div> -->
        </div>
        <div class="flex flex-wrap gap-2">
          <button class="btn-secondary" type="button" @click="$emit('open-config')">前往配置管理</button>
          <button class="btn-primary" type="button" :disabled="disabled" @click="$emit('connect-outlook')">连接 Outlook (Graph)</button>
        </div>
      </div>
    </div>

    <div v-if="form.provider === 'outlook'" class="flex justify-end">
      <button class="btn-secondary" type="button" @click="$emit('cancel')">取消</button>
    </div>

    <template v-else>
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">IMAP Host</label>
          <input v-model="form.imap_host" class="field" :placeholder="currentProviderPreset.imap_host" :disabled="disabled || form.provider !== 'custom'" />
        </div>
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">IMAP Port</label>
          <input v-model.number="form.imap_port" class="field" type="number" :disabled="disabled || form.provider !== 'custom'" />
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">IMAP 用户名</label>
          <input v-model="form.imap_username" class="field" :placeholder="form.email_address || 'your@example.com'" :disabled="disabled" />
        </div>
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">
            {{ isEdit ? '更新授权码 / 密码' : '授权码 / 密码' }}
          </label>
          <input
            v-model="form.imap_password"
            class="field"
            type="password"
            :placeholder="isEdit ? '留空表示不修改' : currentProviderPreset.password_placeholder"
            :disabled="disabled"
            :required="!isEdit"
          />
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-3">
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">监听目录</label>
          <input v-model="form.mailbox_folder" class="field" placeholder="INBOX" :disabled="disabled" />
        </div>
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">轮询 / 兜底间隔</label>
          <input v-model.number="form.listen_interval_seconds" class="field" type="number" min="3" :disabled="disabled" />
        </div>
        <div class="flex items-end">
          <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
            <input v-model="form.use_ssl" type="checkbox" />
            使用 SSL
          </label>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="mb-2 block text-sm font-medium text-slate-600">监听方式</label>
          <select v-model="form.listener_mode" class="field" :disabled="disabled">
            <option value="polling">纯轮询</option>
            <option value="idle_fallback">IMAP IDLE + 低频轮询兜底</option>
          </select>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-7 text-slate-500">
          `IDLE + 兜底` 仅适用于支持 IMAP IDLE 的服务端；如果连接不稳定，可切回纯轮询。
        </div>
      </div>

      <div class="flex flex-wrap items-center justify-between gap-3 rounded-[24px] border border-sky-100 bg-sky-50/70 px-5 py-4">
        <label class="inline-flex items-center gap-3 text-sm text-slate-700">
          <input v-model="form.is_active" type="checkbox" />
          保存后立即开始监听这个邮箱
        </label>
        <div class="flex gap-3">
          <button class="btn-secondary" type="button" @click="$emit('cancel')">取消</button>
          <button class="btn-primary" type="submit" :disabled="disabled">{{ submitLabel }}</button>
        </div>
      </div>
    </template>
  </form>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { mailAccountsApi } from '@/api/modules/mailAccounts'
import type { MailAccountItem, MailAccountPayload, MailProviderPresetItem } from '@/types/api'

const emit = defineEmits<{
  submit: [payload: MailAccountPayload]
  cancel: []
  'open-config': []
  'connect-outlook': []
}>()

const props = withDefaults(
  defineProps<{
    initialValue?: MailAccountItem | null
    disabled?: boolean
    submitLabel?: string
  }>(),
  {
    initialValue: null,
    disabled: false,
    submitLabel: '保存邮箱账户',
  },
)

const form = reactive({
  owner_email: '',
  email_address: '',
  display_name: '',
  provider: 'qq',
  imap_host: 'imap.qq.com',
  imap_port: 993,
  imap_username: '',
  imap_password: '',
  mailbox_folder: 'INBOX',
  use_ssl: true,
  is_active: true,
  listen_interval_seconds: 5,
  listener_mode: 'polling',
})

const providerPresets = ref<MailProviderPresetItem[]>([])
const fallbackProviderPresets: MailProviderPresetItem[] = [
  {
    id: 'qq',
    label: 'QQ 邮箱',
    imap_host: 'imap.qq.com',
    imap_port: 993,
    auth_type: 'password',
    sync_mode: 'imap',
    auth_hint: '开启 IMAP 后使用客户端授权码登录。',
    password_placeholder: 'QQ 邮箱 IMAP 授权码',
    supports_app_password: true,
    suggested_folders: ['INBOX', 'Sent', 'Drafts', 'Spam'],
  },
  {
    id: 'gmail',
    label: 'Gmail',
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    auth_type: 'password',
    sync_mode: 'imap',
    auth_hint: '建议开启两步验证后使用应用专用密码。',
    password_placeholder: 'Gmail 应用专用密码',
    supports_app_password: true,
    suggested_folders: ['INBOX', '[Gmail]/Sent Mail', '[Gmail]/Drafts', '[Gmail]/Spam'],
  },
  {
    id: 'outlook',
    label: 'Outlook / Microsoft 365',
    imap_host: 'graph.microsoft.com',
    imap_port: 443,
    auth_type: 'oauth2',
    sync_mode: 'graph',
    auth_hint: 'Outlook.com / Microsoft 365 通过 Microsoft Graph OAuth2 授权，不再使用 IMAP Basic Auth。',
    password_placeholder: '通过 Microsoft 登录授权',
    supports_app_password: false,
    suggested_folders: ['INBOX', 'Sent Items', 'Drafts', 'Junk Email'],
  },
  {
    id: '163',
    label: '网易 163 邮箱',
    imap_host: 'imap.163.com',
    imap_port: 993,
    auth_type: 'password',
    sync_mode: 'imap',
    auth_hint: '需先开启 IMAP，并使用客户端授权密码。',
    password_placeholder: '网易 163 邮箱客户端授权密码',
    supports_app_password: true,
    suggested_folders: ['INBOX', 'Sent', 'Drafts', 'Spam'],
  },
  {
    id: 'aliyun',
    label: '阿里云邮箱',
    imap_host: 'imap.aliyun.com',
    imap_port: 993,
    auth_type: 'password',
    sync_mode: 'imap',
    auth_hint: '企业邮箱通常使用密码或客户端授权密码。',
    password_placeholder: '阿里云邮箱密码或客户端授权密码',
    supports_app_password: true,
    suggested_folders: ['INBOX', 'Sent', 'Drafts', 'Spam'],
  },
  {
    id: 'custom',
    label: '自定义 IMAP',
    imap_host: 'imap.example.com',
    imap_port: 993,
    auth_type: 'password',
    sync_mode: 'imap',
    auth_hint: '填写实际 IMAP 主机、端口和账号信息。',
    password_placeholder: 'IMAP 密码或授权码',
    supports_app_password: false,
    suggested_folders: ['INBOX'],
  },
]

const isEdit = computed(() => Boolean(props.initialValue))
const presets = computed(() => (providerPresets.value.length ? providerPresets.value : fallbackProviderPresets))
const providerOptions = computed(() =>
  presets.value.map((provider) => ({ value: provider.id, label: provider.label })),
)
const currentProviderPreset = computed(
  () => presets.value.find((provider) => provider.id === form.provider) ?? fallbackProviderPresets[fallbackProviderPresets.length - 1],
)

watch(
  () => form.provider,
  (provider) => {
    if (provider !== 'custom' && provider !== 'outlook') {
      const preset = presets.value.find((item) => item.id === provider) ?? fallbackProviderPresets[0]
      form.imap_host = preset.imap_host
      form.imap_port = preset.imap_port
      if (!form.imap_username && form.email_address) form.imap_username = form.email_address
    }
  },
)

watch(
  () => form.email_address,
  (value) => {
    if (form.provider !== 'custom' && form.provider !== 'outlook') form.imap_username = value
    if (!form.owner_email.trim()) form.owner_email = value
  },
)

watch(
  () => props.initialValue,
  (value) => {
    if (!value) {
      form.owner_email = ''
      form.email_address = ''
      form.display_name = ''
      form.provider = 'qq'
      form.imap_host = fallbackProviderPresets[0].imap_host
      form.imap_port = fallbackProviderPresets[0].imap_port
      form.imap_username = ''
      form.imap_password = ''
      form.mailbox_folder = 'INBOX'
      form.use_ssl = true
      form.is_active = true
      form.listen_interval_seconds = 5
      form.listener_mode = 'polling'
      return
    }
    form.owner_email = value.owner_email
    form.email_address = value.email_address
    form.display_name = value.display_name ?? ''
    form.provider = value.provider
    form.imap_host = value.imap_host
    form.imap_port = value.imap_port
    form.imap_username = value.imap_username
    form.imap_password = ''
    form.mailbox_folder = value.mailbox_folder
    form.use_ssl = value.use_ssl
    form.is_active = value.is_active
    form.listen_interval_seconds = value.listen_interval_seconds
    form.listener_mode = value.listener_mode ?? 'polling'
  },
  { immediate: true },
)

onMounted(async () => {
  try {
    providerPresets.value = await mailAccountsApi.listProviders()
  } catch {
    providerPresets.value = fallbackProviderPresets
  }
})

function submit(): void {
  if (form.provider === 'outlook') {
    emit('connect-outlook')
    return
  }
  emit('submit', {
    owner_email: form.owner_email.trim() || null,
    email_address: form.email_address.trim(),
    display_name: form.display_name.trim() || null,
    provider: form.provider,
    imap_host: form.imap_host.trim() || null,
    imap_port: form.imap_port,
    imap_username: form.imap_username.trim() || null,
    imap_password: form.imap_password,
    mailbox_folder: form.mailbox_folder.trim() || 'INBOX',
    use_ssl: form.use_ssl,
    is_active: form.is_active,
    listen_interval_seconds: form.listen_interval_seconds,
    listener_mode: form.listener_mode,
  })
}
</script>
