import apiClient from '@/api/client'
import type {
  MailAccountDeleteResult,
  MailAccountItem,
  MailAccountPayload,
  MailAccountSyncResult,
  MailAccountTestResult,
} from '@/types/api'

export const mailAccountsApi = {
  async list(): Promise<MailAccountItem[]> {
    const { data } = await apiClient.get<MailAccountItem[]>('/api/mail-accounts')
    return data
  },
  async create(payload: MailAccountPayload): Promise<MailAccountItem> {
    const { data } = await apiClient.post<MailAccountItem>('/api/mail-accounts', payload)
    return data
  },
  async update(id: string, payload: Partial<MailAccountPayload>): Promise<MailAccountItem> {
    const { data } = await apiClient.put<MailAccountItem>(`/api/mail-accounts/${id}`, payload)
    return data
  },
  async remove(id: string): Promise<MailAccountDeleteResult> {
    const { data } = await apiClient.delete<MailAccountDeleteResult>(`/api/mail-accounts/${id}`)
    return data
  },
  async test(id: string): Promise<MailAccountTestResult> {
    const { data } = await apiClient.post<MailAccountTestResult>(`/api/mail-accounts/${id}/test`, undefined, {
      timeout: 30000,
    })
    return data
  },
  async sync(id: string): Promise<MailAccountSyncResult> {
    const { data } = await apiClient.post<MailAccountSyncResult>(`/api/mail-accounts/${id}/sync`, undefined, {
      timeout: 60000,
    })
    return data
  },
}
