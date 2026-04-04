import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { authApi } from '@/api/modules/auth'

const TOKEN_KEY = 'phishing_console_token'
const USERNAME_KEY = 'phishing_console_username'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const username = ref<string>(localStorage.getItem(USERNAME_KEY) || 'admin')
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => Boolean(token.value))

  function setToken(value: string | null): void {
    token.value = value
    if (value) {
      localStorage.setItem(TOKEN_KEY, value)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function setUsername(value: string): void {
    username.value = value
    localStorage.setItem(USERNAME_KEY, value)
  }

  async function login(payload: { username: string; password: string }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await authApi.login(payload)
      setUsername(response.username)
      setToken(response.access_token)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Login failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    setToken(null)
  }

  async function changePassword(payload: {
    current_username: string
    current_password: string
    new_username: string
    new_password: string
  }): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await authApi.changePassword(payload)
      setUsername(response.username)
      setToken(response.access_token)
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Password change failed'
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    token,
    username,
    loading,
    error,
    isAuthenticated,
    setToken,
    setUsername,
    login,
    changePassword,
    logout,
  }
})
