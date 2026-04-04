export const API_BASE_URL_STORAGE_KEY = 'https://pinkdolphin.kkk1eran.top'

export function getApiBaseUrl(): string {
  const runtimeOverride =
    typeof window !== 'undefined' ? window.localStorage.getItem(API_BASE_URL_STORAGE_KEY)?.trim() : ''
  if (runtimeOverride) return trimTrailingSlash(runtimeOverride)

  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  if (configured) return trimTrailingSlash(configured)

  return ''
}

export function setApiBaseUrlOverride(value: string): void {
  if (typeof window === 'undefined') return
  const normalized = trimTrailingSlash(value.trim())
  if (normalized) {
    window.localStorage.setItem(API_BASE_URL_STORAGE_KEY, normalized)
    return
  }
  window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY)
}

export function clearApiBaseUrlOverride(): void {
  if (typeof window === 'undefined') return
  window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY)
}

function trimTrailingSlash(value: string): string {
  if (!value || value === '/') return value
  return value.replace(/\/+$/, '')
}
