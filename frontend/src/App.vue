<template>
  <RouterView />
  <div
    v-if="!systemStore.backendAvailable"
    class="fixed right-4 bottom-4 z-[100] w-[min(420px,calc(100vw-2rem))] rounded-[28px] border border-red-200 bg-white/96 p-5 shadow-[0_20px_60px_rgba(16,24,40,0.16)]"
  >
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="inline-flex rounded-full bg-red-50 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-red-600">Backend Offline</p>
        <p class="mt-3 text-base font-semibold tracking-[-0.03em] text-slate-950">后端健康检查失败</p>
        <p class="mt-2 text-sm leading-6 text-slate-500">
          页面不再阻断操作，但当前请求可能失败。{{ systemStore.error || '请检查后端服务与代理配置。' }}
        </p>
        <p class="mt-2 text-xs text-slate-400">最后检查：{{ systemStore.lastCheckedAt || '--' }}</p>
      </div>
      <button class="btn-secondary shrink-0" type="button" :disabled="systemStore.checking" @click="retry">
        {{ systemStore.checking ? '检查中...' : '重试' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import { useSystemStore } from '@/stores/system'

const systemStore = useSystemStore()
let timer: number | undefined

async function retry(): Promise<void> {
  await systemStore.checkBackend()
}

onMounted(async () => {
  await systemStore.checkBackend()
  timer = window.setInterval(() => {
    void systemStore.checkBackend()
  }, 15000)
})

onUnmounted(() => {
  if (timer) window.clearInterval(timer)
})
</script>
