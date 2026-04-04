import apiClient from '@/api/client'
import type { DashboardSummary } from '@/types/api'

export const dashboardApi = {
  async getSummary(): Promise<DashboardSummary> {
    const { data } = await apiClient.get<DashboardSummary>('/api/dashboard/summary')
    return data
  },
}

