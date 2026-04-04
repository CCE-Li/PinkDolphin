import apiClient from '@/api/client'

export const systemApi = {
  async health(): Promise<{ status: string }> {
    const { data } = await apiClient.get<{ status: string }>('/health')
    return data
  },
}

