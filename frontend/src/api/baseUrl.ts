export const API_BASE_URL_STORAGE_KEY = 'http://localhost:8002'

const LEGACY_API_BASE_URL_STORAGE_KEYS = ['http://localhost:8002']
// const API_PREFIX = '/api'
const API_PREFIX = ''

export function getApiBaseUrl(): string {
  const runtimeOverride = getStoredApiBaseUrl()
  if (runtimeOverride) return trimTrailingSlash(runtimeOverride)

  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  if (configured) return trimTrailingSlash(configured)

  return ''
}

export function resolveApiRequestUrl(value: string): string {
  const normalizedPath = normalizeRequestPath(value)
  if (!normalizedPath || isAbsoluteUrl(normalizedPath)) return normalizedPath

  const configuredBaseUrl = getApiBaseUrl()
  if (!configuredBaseUrl) return normalizedPath

  const baseUrl = trimTrailingSlash(configuredBaseUrl)
  const requestPath = shouldDeduplicateApiPrefix(baseUrl, normalizedPath)
    ? normalizedPath.slice(API_PREFIX.length)
    : normalizedPath

  if (normalizedPath === '/health') {
    return joinUrl(stripApiSuffix(baseUrl), normalizedPath)
  }

  return joinUrl(baseUrl, requestPath)
}

export function setApiBaseUrlOverride(value: string): void {
  if (typeof window === 'undefined') return
  const normalized = trimTrailingSlash(value.trim())
  if (normalized) {
    window.localStorage.setItem(API_BASE_URL_STORAGE_KEY, normalized)
    return
  }
  clearStoredApiBaseUrl()
}

export function clearApiBaseUrlOverride(): void {
  if (typeof window === 'undefined') return
  clearStoredApiBaseUrl()
}

function getStoredApiBaseUrl(): string {
  if (typeof window === 'undefined') return ''

  const primaryValue = window.localStorage.getItem(API_BASE_URL_STORAGE_KEY)?.trim()
  if (primaryValue) return primaryValue

  for (const legacyKey of LEGACY_API_BASE_URL_STORAGE_KEYS) {
    const legacyValue = window.localStorage.getItem(legacyKey)?.trim()
    if (legacyValue) return legacyValue
  }

  return ''
}

function clearStoredApiBaseUrl(): void {
  window.localStorage.removeItem(API_BASE_URL_STORAGE_KEY)
  for (const legacyKey of LEGACY_API_BASE_URL_STORAGE_KEYS) {
    window.localStorage.removeItem(legacyKey)
  }
}

function normalizeRequestPath(value: string): string {
  const trimmed = value.trim()
  if (!trimmed || isAbsoluteUrl(trimmed)) return trimmed
  if (trimmed.startsWith('?') || trimmed.startsWith('#')) return trimmed
  return trimmed.startsWith('/') ? trimmed : `/${trimmed}`
}

function shouldDeduplicateApiPrefix(baseUrl: string, requestPath: string): boolean {
  return hasApiSuffix(baseUrl) && requestPath.startsWith(`${API_PREFIX}/`)
}

function hasApiSuffix(value: string): boolean {
  return value === API_PREFIX || value.endsWith(API_PREFIX)
}

function stripApiSuffix(value: string): string {
  if (!hasApiSuffix(value)) return value
  if (value === API_PREFIX) return ''
  return value.slice(0, -API_PREFIX.length)
}

function joinUrl(baseUrl: string, requestPath: string): string {
  if (!baseUrl) return requestPath.startsWith('/') ? requestPath : `/${requestPath}`
  return `${trimTrailingSlash(baseUrl)}${requestPath.startsWith('/') ? requestPath : `/${requestPath}`}`
}

function isAbsoluteUrl(value: string): boolean {
  return /^[a-z][a-z\d+.-]*:\/\//i.test(value) || value.startsWith('//')
}

function trimTrailingSlash(value: string): string {
  if (!value || value === '/') return value
  return value.replace(/\/+$/, '')
}
