import { ref } from 'vue'

export function useAsyncState<T>() {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function run(task: () => Promise<T>): Promise<void> {
    loading.value = true
    error.value = null
    try {
      data.value = await task()
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Unexpected error'
    } finally {
      loading.value = false
    }
  }

  return {
    data,
    loading,
    error,
    run,
  }
}
