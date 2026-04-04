import apiClient from '@/api/client'
import type { AllowlistItem, AllowlistPayload } from '@/types/api'

export const allowlistsApi = {
  async list(): Promise<AllowlistItem[]> {
    const { data } = await apiClient.get<AllowlistItem[]>('/api/allowlists')
    return data
  },
  async create(payload: AllowlistPayload): Promise<AllowlistItem> {
    const { data } = await apiClient.post<AllowlistItem>('/api/allowlists', payload)
    return data
  },
  async update(id: string, payload: Partial<AllowlistPayload>): Promise<AllowlistItem> {
    const { data } = await apiClient.put<AllowlistItem>(`/api/allowlists/${id}`, payload)
    return data
  },
}
