import apiClient from '@/api/client'
import type { RuleItem, RulePayload } from '@/types/api'

export const rulesApi = {
  async list(): Promise<RuleItem[]> {
    const { data } = await apiClient.get<RuleItem[]>('/api/rules')
    return data
  },
  async create(payload: RulePayload): Promise<RuleItem> {
    const { data } = await apiClient.post<RuleItem>('/api/rules', payload)
    return data
  },
  async update(id: string, payload: Partial<RulePayload>): Promise<RuleItem> {
    const { data } = await apiClient.put<RuleItem>(`/api/rules/${id}`, payload)
    return data
  },
}

