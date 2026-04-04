<template>
  <section class="space-y-6">
    <div class="panel">
      <div class="panel-header">
        <h2 class="text-xl font-semibold tracking-[-0.03em] text-slate-950">配置管理</h2>
        <button class="btn-secondary" type="button" @click="tipsOpen = !tipsOpen">
          {{ tipsOpen ? '收起 Tips' : 'Tips' }}
        </button>
      </div>
      <div class="panel-body space-y-4">
        <div v-if="tipsOpen" class="rounded-[24px] border border-sky-100 bg-sky-50/70 p-5 text-sm leading-7 text-slate-600">
          <div>当前页面只展示允许动态调整的配置，不展示部署层配置。</div>
          <div class="mt-1">每项配置都可以单独编辑；保存后会写回 `backend/.env`，后续请求使用新值。</div>
          <div class="mt-1">文件路径：{{ envFile?.path || '--' }}</div>
        </div>

        <LoadingState v-if="loading" message="正在加载环境配置..." />
        <ErrorState v-else-if="error" :message="error" @retry="load" />
        <template v-else>
          <div class="space-y-6">
            <section v-for="group in fieldGroups" :key="group.title" class="panel">
              <div class="panel-header">
                <h3 class="text-lg font-semibold text-slate-900">{{ group.title }}</h3>
              </div>
              <div class="panel-body space-y-3">
                <article
                  v-for="item in group.items"
                  :key="item.key"
                  class="rounded-[24px] border border-slate-200 bg-white px-5 py-4"
                >
                  <div class="flex items-center justify-between gap-4">
                    <div class="min-w-0 flex-1 text-sm text-slate-600">
                      <span class="text-slate-900">{{ item.label }}</span>
                      <span class="text-slate-400">（{{ item.key }}）</span>
                      <span class="mx-2 text-slate-300">:</span>
                      <span class="break-all font-semibold text-slate-950">{{ displayValue(item.key) }}</span>
                    </div>
                    <button class="btn-secondary shrink-0" type="button" @click="startEdit(item.key)">
                      {{ editingKey === item.key ? '取消' : '编辑' }}
                    </button>
                  </div>

                  <div v-if="editingKey === item.key" class="mt-4 space-y-4 border-t border-slate-100 pt-4">
                    <div class="text-sm text-slate-500">{{ item.description }}</div>

                    <select
                      v-if="item.kind === 'select' || item.kind === 'boolean'"
                      v-model="editValue"
                      class="field"
                    >
                      <option v-for="option in item.options || []" :key="option.value" :value="option.value">
                        {{ option.label }}
                      </option>
                    </select>

                    <textarea
                      v-else-if="item.multiline"
                      v-model="editValue"
                      class="min-h-[120px] w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-mono text-sm text-slate-700 outline-none transition focus:border-sky-300"
                      spellcheck="false"
                    />

                    <input
                      v-else
                      v-model="editValue"
                      class="field"
                      :type="item.secret ? 'password' : item.kind === 'number' ? 'number' : 'text'"
                      :placeholder="item.placeholder"
                    />

                    <div class="flex justify-end gap-3">
                      <button class="btn-secondary" type="button" :disabled="saving" @click="cancelEdit">取消</button>
                      <button class="btn-primary" type="button" :disabled="saving" @click="saveItem(item.key)">
                        {{ saving ? '保存中...' : '保存' }}
                      </button>
                    </div>
                  </div>
                </article>
              </div>
            </section>
          </div>

          <p v-if="message" class="text-sm text-sky-600">{{ message }}</p>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { configManagementApi } from '@/api/modules/configManagement'
import ErrorState from '@/components/ErrorState.vue'
import LoadingState from '@/components/LoadingState.vue'
import type { EnvFileItem } from '@/types/api'

type ConfigField = {
  key: string
  label: string
  description: string
  placeholder?: string
  multiline?: boolean
  secret?: boolean
  kind?: 'text' | 'number' | 'boolean' | 'select'
  options?: Array<{ label: string; value: string }>
}

type ConfigGroup = {
  title: string
  items: ConfigField[]
}

const fieldGroups: ConfigGroup[] = [
  {
    title: 'LLM',
    items: [
      {
        key: 'LLM_ANALYZER_ENABLED',
        label: 'LLM 分析开关',
        description: '控制是否启用 LLM 分析器。',
        kind: 'boolean',
        options: [
          { label: '开启', value: 'true' },
          { label: '关闭', value: 'false' },
        ],
      },
      {
        key: 'LLM_PROVIDER_MODE',
        label: '提供方模式',
        description: '通常为 real 或 mock。',
        kind: 'select',
        options: [
          { label: '真实模式', value: 'real' },
          { label: '模拟模式', value: 'mock' },
        ],
      },
      { key: 'LLM_MODEL', label: '模型名称', description: '例如 DeepSeek、OpenAI 兼容模型名。', placeholder: 'deepseek-ai/DeepSeek-V3.2' },
      { key: 'LLM_API_KEY', label: 'API Key', description: 'LLM 请求使用的密钥。', placeholder: 'sk-...', secret: true },
      { key: 'LLM_BASE_URL', label: 'Base URL', description: '兼容 OpenAI 的推理服务地址。', placeholder: 'https://api.siliconflow.cn/v1' },
      { key: 'LLM_TIMEOUT_SECONDS', label: '超时秒数', description: 'LLM 请求最大等待时间。', placeholder: '600', kind: 'number' },
      { key: 'LLM_MAX_INPUT_CHARS', label: '最大输入字符数', description: '发给模型的正文裁剪上限。', placeholder: '6000', kind: 'number' },
      { key: 'LLM_TEMPERATURE', label: 'Temperature', description: '模型采样温度。', placeholder: '0', kind: 'number' },
    ],
  },
  {
    title: 'URL 扫描',
    items: [
      {
        key: 'URL_SCAN_PROVIDER',
        label: 'URL 扫描提供方',
        description: '例如 mock 或 google_safe_browsing。',
        kind: 'select',
        options: [
          { label: 'Google Safe Browsing', value: 'google_safe_browsing' },
          { label: 'Mock', value: 'mock' },
        ],
      },
      { key: 'SAFEBROWSING_API_KEY', label: 'Safe Browsing Key', description: 'Google Safe Browsing API 密钥。', placeholder: 'AIza...', secret: true },
      { key: 'SAFEBROWSING_TIMEOUT_SECONDS', label: 'URL 扫描超时', description: 'URL 扫描请求超时秒数。', placeholder: '10', kind: 'number' },
    ],
  },
  {
    title: '附件扫描',
    items: [
      {
        key: 'ATTACHMENT_SCAN_PROVIDER',
        label: '附件扫描提供方',
        description: '例如 mock 或 virustotal。',
        kind: 'select',
        options: [
          { label: 'VirusTotal', value: 'virustotal' },
          { label: 'Mock', value: 'mock' },
        ],
      },
      { key: 'VIRUSTOTAL_API_KEY', label: 'VirusTotal Key', description: 'VirusTotal API 密钥。', placeholder: 'your_api_key', secret: true },
      { key: 'VIRUSTOTAL_TIMEOUT_SECONDS', label: '附件扫描超时', description: 'VirusTotal 请求超时秒数。', placeholder: '30', kind: 'number' },
      { key: 'VIRUSTOTAL_POLL_ATTEMPTS', label: '轮询次数', description: '上传附件后最多轮询几次。', placeholder: '4', kind: 'number' },
      { key: 'VIRUSTOTAL_POLL_INTERVAL_SECONDS', label: '轮询间隔', description: '附件分析结果轮询间隔秒数。', placeholder: '4', kind: 'number' },
      {
        key: 'VIRUSTOTAL_UPLOAD_ENABLED',
        label: '允许上传附件',
        description: '当本地没有 hash 报告时，是否上传附件到 VirusTotal。',
        kind: 'boolean',
        options: [
          { label: '开启', value: 'true' },
          { label: '关闭', value: 'false' },
        ],
      },
    ],
  },
  {
    title: '运行策略',
    items: [
      {
        key: 'LOG_LEVEL',
        label: '日志级别',
        description: '后端日志级别。',
        kind: 'select',
        options: [
          { label: 'DEBUG', value: 'DEBUG' },
          { label: 'INFO', value: 'INFO' },
          { label: 'WARNING', value: 'WARNING' },
          { label: 'ERROR', value: 'ERROR' },
        ],
      },
      { key: 'MAX_UPLOAD_SIZE_MB', label: '最大上传大小', description: '邮件上传接口允许的文件大小上限。', placeholder: '10', kind: 'number' },
      { key: 'ENABLED_ANALYZERS', label: '启用分析器', description: 'JSON 数组格式。', placeholder: '["header_auth","content_rule","url","attachment","behavior","llm"]', multiline: true },
      { key: 'ANALYZER_WEIGHTS', label: '分析器权重', description: 'JSON 对象格式。', placeholder: '{"header_auth":1.0,"content_rule":1.2}', multiline: true },
    ],
  },
]

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const message = ref<string | null>(null)
const envFile = ref<EnvFileItem | null>(null)
const configMap = ref<Record<string, string>>({})
const editingKey = ref<string | null>(null)
const editValue = ref('')
const tipsOpen = ref(false)

async function load(): Promise<void> {
  loading.value = true
  error.value = null
  message.value = null
  try {
    envFile.value = await configManagementApi.getEnvFile()
    configMap.value = parseEnvContent(envFile.value.content)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load env file'
  } finally {
    loading.value = false
  }
}

function parseEnvContent(content: string): Record<string, string> {
  const result: Record<string, string> = {}
  for (const line of content.split('\n')) {
    const trimmed = line.trim()
    if (!trimmed || trimmed.startsWith('#')) continue
    const index = line.indexOf('=')
    if (index < 0) continue
    const key = line.slice(0, index).trim()
    const value = line.slice(index + 1).trim()
    result[key] = value
  }
  return result
}

function stringifyEnvContent(values: Record<string, string>): string {
  const lines: string[] = []
  for (const group of fieldGroups) {
    for (const item of group.items) {
      lines.push(`${item.key}=${values[item.key] ?? ''}`)
    }
  }
  return `${lines.join('\n')}\n`
}

function displayValue(key: string): string {
  const value = configMap.value[key] ?? ''
  if (!value) return '--'
  if (key.includes('API_KEY')) {
    return `${value.slice(0, 6)}***${value.slice(-4)}`
  }
  if (value === 'true') return '开启'
  if (value === 'false') return '关闭'
  return value
}

function startEdit(key: string): void {
  if (editingKey.value === key) {
    cancelEdit()
    return
  }
  editingKey.value = key
  editValue.value = configMap.value[key] ?? ''
  message.value = null
}

function cancelEdit(): void {
  editingKey.value = null
  editValue.value = ''
}

async function saveItem(key: string): Promise<void> {
  saving.value = true
  error.value = null
  message.value = null
  try {
    const normalizedValue =
      editValue.value === null || editValue.value === undefined
        ? ''
        : String(editValue.value).trim()
    const next = { ...configMap.value, [key]: normalizedValue }
    const content = stringifyEnvContent(next)
    envFile.value = await configManagementApi.updateEnvFile(content)
    configMap.value = parseEnvContent(envFile.value.content)
    message.value = `${key} 已更新`
    cancelEdit()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to save config item'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
