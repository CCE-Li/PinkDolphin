import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { systemApi } from '@/api/modules/system'

export const useSystemStore = defineStore('system', () => {
  const backendAvailable = ref(true)
  const checking = ref(false)
  const lastCheckedAt = ref<string | null>(null)
  const error = ref<string | null>(null)

  const statusLabel = computed(() => {
    if (checking.value && !lastCheckedAt.value) return 'checking'
    return backendAvailable.value ? 'online' : 'offline'
  })

  async function checkBackend(): Promise<boolean> {
    checking.value = true
    try {
      const response = await systemApi.health()
      backendAvailable.value = response.status === 'ok'
      error.value = backendAvailable.value ? null : 'Backend health check failed'
      return backendAvailable.value
    } catch (err) {
      backendAvailable.value = false
      error.value = err instanceof Error ? err.message : 'Backend unavailable'
      return false
    } finally {
      checking.value = false
      lastCheckedAt.value = new Date().toISOString()
    }
  }

  return {
    backendAvailable,
    checking,
    lastCheckedAt,
    error,
    statusLabel,
    checkBackend,
  }
})

