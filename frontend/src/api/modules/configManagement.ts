import apiClient from '@/api/client'
import type { EnvFileItem } from '@/types/api'

export const configManagementApi = {
  async getEnvFile(): Promise<EnvFileItem> {
    const { data } = await apiClient.get<EnvFileItem>('/api/config-management/env')
    return data
  },
  async updateEnvFile(content: string): Promise<EnvFileItem> {
    const { data } = await apiClient.put<EnvFileItem>('/api/config-management/env', { content })
    return data
  },
}
