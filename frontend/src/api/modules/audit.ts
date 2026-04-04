import apiClient from '@/api/client'
import type { AuditLogItem } from '@/types/api'

export const auditApi = {
  async list(): Promise<AuditLogItem[]> {
    const { data } = await apiClient.get<AuditLogItem[]>('/api/audit-logs')
    return data
  },
}

