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
          :placeholder="isEdit ? '留空表示不修改' : currentProviderPreset.passwordPlaceholder"
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
        <label class="mb-2 block text-sm font-medium text-slate-600">轮询间隔</label>
        <input v-model.number="form.listen_interval_seconds" class="field" type="number" min="3" :disabled="disabled" />
      </div>
      <div class="flex items-end">
        <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
          <input v-model="form.use_ssl" type="checkbox" />
          使用 SSL
        </label>
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
  </form>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import type { MailAccountItem, MailAccountPayload } from '@/types/api'

const emit = defineEmits<{
  submit: [payload: MailAccountPayload]
  cancel: []
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
})

const providerOptions = [
  { value: 'qq', label: 'QQ 邮箱' },
  { value: 'gmail', label: 'Gmail' },
  { value: 'outlook', label: 'Outlook / Office 365' },
  { value: '163', label: '网易 163 邮箱' },
  { value: 'aliyun', label: '阿里云邮箱' },
  { value: 'custom', label: '自定义 IMAP' },
]

const providerPresets: Record<string, { imap_host: string; imap_port: number; passwordPlaceholder: string }> = {
  qq: { imap_host: 'imap.qq.com', imap_port: 993, passwordPlaceholder: 'QQ 邮箱 IMAP 授权码' },
  gmail: { imap_host: 'imap.gmail.com', imap_port: 993, passwordPlaceholder: 'Gmail 应用专用密码' },
  outlook: { imap_host: 'outlook.office365.com', imap_port: 993, passwordPlaceholder: 'Outlook / Office 365 密码或应用密码' },
  '163': { imap_host: 'imap.163.com', imap_port: 993, passwordPlaceholder: '网易 163 邮箱客户端授权密码' },
  aliyun: { imap_host: 'imap.aliyun.com', imap_port: 993, passwordPlaceholder: '阿里云邮箱密码或客户端授权密码' },
  custom: { imap_host: 'imap.example.com', imap_port: 993, passwordPlaceholder: 'IMAP 密码或授权码' },
}

const isEdit = computed(() => Boolean(props.initialValue))
const currentProviderPreset = computed(() => providerPresets[form.provider] ?? providerPresets.custom)

watch(
  () => form.provider,
  (provider) => {
    if (provider !== 'custom') {
      const preset = providerPresets[provider] ?? providerPresets.qq
      form.imap_host = preset.imap_host
      form.imap_port = preset.imap_port
      if (!form.imap_username && form.email_address) form.imap_username = form.email_address
    }
  },
)

watch(
  () => form.email_address,
  (value) => {
    if (form.provider !== 'custom') form.imap_username = value
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
      form.imap_host = providerPresets.qq.imap_host
      form.imap_port = providerPresets.qq.imap_port
      form.imap_username = ''
      form.imap_password = ''
      form.mailbox_folder = 'INBOX'
      form.use_ssl = true
      form.is_active = true
      form.listen_interval_seconds = 5
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
  },
  { immediate: true },
)

function submit(): void {
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
  })
}
</script>
