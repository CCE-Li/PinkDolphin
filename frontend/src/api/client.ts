import axios from 'axios'

function resolveApiBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL?.trim()
  if (configured) return configured

  if (typeof window === 'undefined') return ''

  const { port } = window.location
  if (port === '5173' || port === '4173') {
    return 'http://127.0.0.1:8001'
  }

  return ''
}

const apiClient = axios.create({
  baseURL: resolveApiBaseUrl(),
  timeout: 10000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('phishing_console_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      'Request failed'
    return Promise.reject(new Error(message))
  },
)

export default apiClient
