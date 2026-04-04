<template>
  <section class="space-y-6">
    <div class="flex items-end justify-between gap-4">
      <button class="btn-primary" type="button" @click="openCreate">新增白名单</button>
    </div>

    <LoadingState v-if="loading" message="正在加载隐私白名单..." />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <template v-else>
      <div class="grid gap-4 md:grid-cols-3">
        <StatCard title="总条目" :value="items.length" subtitle="已配置的隐私规则" tone="neutral" />
        <StatCard title="启用中" :value="activeCount" subtitle="当前会生效的条目" tone="success" />
        <StatCard title="发件人类" :value="senderScopedCount" subtitle="可定制 URL/附件/LLM 跳过策略" tone="warning" />
      </div>

      <div class="grid gap-6 xl:grid-cols-[1.15fr,0.85fr]">
        <div class="panel">
          <div class="panel-header">
            <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">白名单条目</h2>
          </div>
          <div class="panel-body">
            <EmptyState
              v-if="!items.length"
              title="还没有隐私白名单"
              description="每条白名单都可以单独控制，命中后是否跳过 URL、附件和大模型扫描。"
            />
            <div v-else class="space-y-4">
              <article
                v-for="item in items"
                :key="item.id"
                class="rounded-[24px] border p-5 transition"
                :class="selectedItem?.id === item.id ? 'border-sky-200 bg-sky-50/60' : 'border-slate-200 bg-white hover:border-sky-100'"
              >
                <div class="flex flex-wrap items-start justify-between gap-4">
                  <div class="min-w-0">
                    <div class="flex flex-wrap items-center gap-2">
                      <span class="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
                        {{ typeLabelMap[item.list_type] || item.list_type }}
                      </span>
                      <span
                        class="rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em]"
                        :class="item.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'"
                      >
                        {{ item.is_active ? '启用' : '停用' }}
                      </span>
                    </div>
                    <div class="mt-3 break-all text-lg font-semibold tracking-[-0.03em] text-slate-950">{{ item.value }}</div>
                    <div class="mt-2 text-sm text-slate-500">创建时间：{{ formatDateTime(item.created_at) }}</div>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button class="btn-secondary" type="button" @click="editItem(item)">编辑</button>
                    <button class="btn-secondary" type="button" @click="toggleActive(item)">
                      {{ item.is_active ? '停用' : '启用' }}
                    </button>
                  </div>
                </div>

                <div class="mt-5 grid gap-3 md:grid-cols-3">
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>跳过 URL</span>
                    <input :checked="item.skip_url_scan" type="checkbox" @change="toggleScan(item, 'skip_url_scan', $event)" />
                  </label>
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>跳过附件</span>
                    <input :checked="item.skip_attachment_scan" type="checkbox" @change="toggleScan(item, 'skip_attachment_scan', $event)" />
                  </label>
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>跳过 LLM</span>
                    <input :checked="item.skip_llm_scan" type="checkbox" @change="toggleScan(item, 'skip_llm_scan', $event)" />
                  </label>
                </div>
              </article>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div ref="formPanelRef" class="panel">
            <div class="panel-header">
              <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">{{ editingItem ? '编辑白名单' : '新增白名单' }}</h2>
            </div>
            <div class="panel-body">
              <form class="grid gap-4" @submit.prevent="saveItem">
                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-600">匹配类型</label>
                  <select v-model="form.list_type" class="field" :disabled="submitting">
                    <option value="address">发件人地址</option>
                    <option value="domain">域名</option>
                    <option value="url">链接 URL</option>
                  </select>
                </div>

                <div>
                  <label class="mb-2 block text-sm font-medium text-slate-600">匹配值</label>
                  <input v-model="form.value" class="field" :placeholder="valuePlaceholder" :disabled="submitting" required />
                </div>

                <label class="inline-flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                  <input v-model="form.is_active" type="checkbox" :disabled="submitting" />
                  保存后立即生效
                </label>

                <div class="grid gap-3">
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>命中后跳过 URL 扫描</span>
                    <input v-model="form.skip_url_scan" type="checkbox" :disabled="submitting" />
                  </label>
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>命中后跳过附件扫描</span>
                    <input v-model="form.skip_attachment_scan" type="checkbox" :disabled="submitting" />
                  </label>
                  <label class="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
                    <span>命中后跳过 LLM 扫描</span>
                    <input v-model="form.skip_llm_scan" type="checkbox" :disabled="submitting" />
                  </label>
                </div>

                <div class="flex justify-end gap-3">
                  <button class="btn-secondary" type="button" @click="resetForm">取消</button>
                  <button class="btn-primary" type="submit" :disabled="submitting">
                    {{ editingItem ? '更新白名单' : '创建白名单' }}
                  </button>
                </div>
              </form>

              <p v-if="formMessage" class="mt-4 text-sm text-sky-600">{{ formMessage }}</p>
              <p v-if="formError" class="mt-4 text-sm text-red-600">{{ formError }}</p>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header">
              <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">命中说明</h2>
            </div>
            <div class="panel-body">
              <div class="rounded-[24px] border border-sky-100 bg-sky-50/70 p-5 text-sm leading-7 text-slate-600">
                <div>每条白名单都可以单独控制 URL、附件、LLM 是否继续扫描。</div>
                <div>只有“发件人地址 / 发件人域名”命中时，这些隐私开关才会影响整封邮件的扫描链路。</div>
                <div>如果某封邮件命中了发件人白名单，且对应条目把 URL、附件、LLM 三个开关都打开，则系统直接按安全邮件处理。</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'

import { allowlistsApi } from '@/api/modules/allowlists'
import EmptyState from '@/components/EmptyState.vue'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import StatCard from '@/components/StatCard.vue'
import type { AllowlistItem } from '@/types/api'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref<string | null>(null)
const items = ref<AllowlistItem[]>([])
const selectedItem = ref<AllowlistItem | null>(null)
const editingItem = ref<AllowlistItem | null>(null)
const submitting = ref(false)
const formMessage = ref<string | null>(null)
const formError = ref<string | null>(null)
const formPanelRef = ref<HTMLElement | null>(null)

const form = reactive({
  list_type: 'address',
  value: '',
  is_active: true,
  skip_url_scan: false,
  skip_attachment_scan: false,
  skip_llm_scan: false,
})

const typeLabelMap: Record<string, string> = {
  address: '发件人地址',
  domain: '域名',
  url: '链接 URL',
}

const activeCount = computed(() => items.value.filter((item) => item.is_active).length)
const senderScopedCount = computed(() => items.value.filter((item) => item.list_type === 'address' || item.list_type === 'domain').length)
const valuePlaceholder = computed(() => {
  if (form.list_type === 'domain') return 'example.com'
  if (form.list_type === 'url') return 'https://intranet.example.com/notice'
  return 'trusted.sender@example.com'
})

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  try {
    items.value = await allowlistsApi.list()
    if (selectedItem.value) {
      selectedItem.value = items.value.find((item) => item.id === selectedItem.value?.id) ?? null
    }
    if (editingItem.value) {
      editingItem.value = items.value.find((item) => item.id === editingItem.value?.id) ?? null
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load allowlists'
  } finally {
    loading.value = false
  }
}

async function openCreate(): Promise<void> {
  editingItem.value = null
  selectedItem.value = null
  form.list_type = 'address'
  form.value = ''
  form.is_active = true
  form.skip_url_scan = false
  form.skip_attachment_scan = false
  form.skip_llm_scan = false
  formMessage.value = null
  formError.value = null
  await nextTick()
  formPanelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function editItem(item: AllowlistItem): Promise<void> {
  selectedItem.value = item
  editingItem.value = item
  form.list_type = item.list_type
  form.value = item.value
  form.is_active = item.is_active
  form.skip_url_scan = item.skip_url_scan
  form.skip_attachment_scan = item.skip_attachment_scan
  form.skip_llm_scan = item.skip_llm_scan
  formMessage.value = null
  formError.value = null
  await nextTick()
  formPanelRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function resetForm(): void {
  editingItem.value = null
  form.list_type = 'address'
  form.value = ''
  form.is_active = true
  form.skip_url_scan = false
  form.skip_attachment_scan = false
  form.skip_llm_scan = false
}

async function saveItem(): Promise<void> {
  submitting.value = true
  formMessage.value = null
  formError.value = null
  try {
    const payload = {
      list_type: form.list_type,
      value: form.value.trim(),
      is_active: form.is_active,
      skip_url_scan: form.skip_url_scan,
      skip_attachment_scan: form.skip_attachment_scan,
      skip_llm_scan: form.skip_llm_scan,
    }
    if (editingItem.value) {
      await allowlistsApi.update(editingItem.value.id, payload)
      formMessage.value = '白名单已更新'
    } else {
      await allowlistsApi.create(payload)
      formMessage.value = '白名单已创建'
    }
    resetForm()
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Save failed'
  } finally {
    submitting.value = false
  }
}

async function toggleActive(item: AllowlistItem): Promise<void> {
  formError.value = null
  formMessage.value = null
  try {
    await allowlistsApi.update(item.id, { is_active: !item.is_active })
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Update failed'
  }
}

async function toggleScan(item: AllowlistItem, field: 'skip_url_scan' | 'skip_attachment_scan' | 'skip_llm_scan', event: Event): Promise<void> {
  const checked = (event.target as HTMLInputElement).checked
  formError.value = null
  formMessage.value = null
  try {
    await allowlistsApi.update(item.id, { [field]: checked })
    await load()
  } catch (err) {
    formError.value = err instanceof Error ? err.message : 'Update failed'
  }
}

onMounted(load)
</script>
