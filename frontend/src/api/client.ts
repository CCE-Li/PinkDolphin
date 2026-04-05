import axios from 'axios'
import { resolveApiRequestUrl } from '@/api/baseUrl'

const apiClient = axios.create({
  timeout: 10000,
})

apiClient.interceptors.request.use((config) => {
  if (config.url && !config.baseURL) {
    config.url = resolveApiRequestUrl(config.url)
  }
  const token = localStorage.getItem('phishing_console_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = formatApiErrorMessage(error)
    const normalizedError = new Error(message) as Error & {
      cause?: unknown
      response?: unknown
    }
    normalizedError.cause = error
    normalizedError.response = (error as { response?: unknown })?.response
    return Promise.reject(normalizedError)
  },
)

export default apiClient

function formatApiErrorMessage(error: unknown): string {
  const data = (error as { response?: { data?: { message?: unknown; detail?: unknown } } })?.response?.data
  const message = normalizeErrorDetail(data?.message)
  if (message) return message

  const detail = normalizeErrorDetail(data?.detail)
  if (detail) return detail

  return (error as { message?: string })?.message || 'Request failed'
}

function normalizeErrorDetail(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    const parts = value
      .map((item) => {
        if (typeof item === 'string') return item
        if (!item || typeof item !== 'object') return ''

        const detail = item as { loc?: unknown[]; msg?: string; type?: string }
        const location = Array.isArray(detail.loc) ? detail.loc.join('.') : ''
        return [location, detail.msg || detail.type].filter(Boolean).join(': ')
      })
      .filter(Boolean)

    return parts.join(' | ')
  }
  if (value && typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  return ''
}
