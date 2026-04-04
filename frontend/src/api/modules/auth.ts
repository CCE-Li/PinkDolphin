import apiClient from '@/api/client'
import type { ChangePasswordRequest, LoginRequest, LoginResponse } from '@/types/api'

export const authApi = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/api/auth/login', payload)
    return data
  },
  async changePassword(payload: ChangePasswordRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/api/auth/change-password', payload)
    return data
  },
}
