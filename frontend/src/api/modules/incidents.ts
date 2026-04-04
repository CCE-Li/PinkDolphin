import apiClient from '@/api/client'
import type { IncidentItem } from '@/types/api'

export const incidentsApi = {
  async list(): Promise<IncidentItem[]> {
    const { data } = await apiClient.get<IncidentItem[]>('/api/incidents')
    return data
  },
}

