import axios from 'axios'
import { getApiBaseUrl } from '@/api/baseUrl'

const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
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
