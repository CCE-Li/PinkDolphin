import apiClient from '@/api/client'
import type {
  EmailActionRequest,
  EmailAnalyzeDeferredResponse,
  EmailAnalyzeResponse,
  EmailDetail,
  EmailListItem,
} from '@/types/api'

export const emailsApi = {
  async list(): Promise<EmailListItem[]> {
    const { data } = await apiClient.get<EmailListItem[]>('/api/emails')
    return data
  },
  async getById(id: string): Promise<EmailDetail> {
    const { data } = await apiClient.get<EmailDetail>(`/api/emails/${id}`)
    return data
  },
  async reanalyze(id: string): Promise<EmailAnalyzeResponse | EmailAnalyzeDeferredResponse> {
    const { data } = await apiClient.post<EmailAnalyzeResponse | EmailAnalyzeDeferredResponse>(`/api/emails/${id}/reanalyze`)
    return data
  },
  async action(id: string, payload: EmailActionRequest): Promise<{ action_id: string; status: string }> {
    const { data } = await apiClient.post<{ action_id: string; status: string }>(`/api/emails/${id}/action`, payload)
    return data
  },
  async remove(id: string): Promise<{ email_id: string; status: string }> {
    const { data } = await apiClient.delete<{ email_id: string; status: string }>(`/api/emails/${id}`)
    return data
  },
}
