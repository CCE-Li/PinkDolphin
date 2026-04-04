import apiClient from '@/api/client'
import type { IssueLogItem } from '@/types/api'

export const issueLogsApi = {
  async list(): Promise<IssueLogItem[]> {
    const { data } = await apiClient.get<IssueLogItem[]>('/api/issue-logs')
    return data
  },
}
