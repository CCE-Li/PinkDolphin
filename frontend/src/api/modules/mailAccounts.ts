import apiClient from '@/api/client'
import type {
  MailAccountDeleteResult,
  MailAccountItem,
  MailAccountPayload,
  MailProviderPresetItem,
  MailAccountSyncResult,
  MailAccountTestResult,
  OutlookOAuthStartPayload,
  OutlookOAuthStartResponse,
} from '@/types/api'

export const mailAccountsApi = {
  async list(): Promise<MailAccountItem[]> {
    const { data } = await apiClient.get<MailAccountItem[]>('/api/mail-accounts')
    return data.map(normalizeMailAccount)
  },
  async listProviders(): Promise<MailProviderPresetItem[]> {
    const { data } = await apiClient.get<MailProviderPresetItem[]>('/api/mail-accounts/providers')
    return data
  },
  async startOutlookOAuth(payload: OutlookOAuthStartPayload): Promise<OutlookOAuthStartResponse> {
    const { data } = await requestWithListenerModeFallback((requestPayload) =>
      apiClient.post<OutlookOAuthStartResponse>('/api/mail-accounts/oauth/outlook/start', requestPayload),
      payload,
    )
    return data
  },
  async create(payload: MailAccountPayload): Promise<MailAccountItem> {
    const { data } = await requestWithListenerModeFallback((requestPayload) =>
      apiClient.post<MailAccountItem>('/api/mail-accounts', requestPayload),
      payload,
    )
    return normalizeMailAccount(data)
  },
  async update(id: string, payload: Partial<MailAccountPayload>): Promise<MailAccountItem> {
    const { data } = await requestWithListenerModeFallback((requestPayload) =>
      apiClient.put<MailAccountItem>(`/api/mail-accounts/${id}`, requestPayload),
      payload,
    )
    return normalizeMailAccount(data)
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

async function requestWithListenerModeFallback<TPayload extends { listener_mode?: string | null }, TResponse>(
  request: (payload: TPayload | Omit<TPayload, 'listener_mode'>) => Promise<{ data: TResponse }>,
  payload: TPayload,
): Promise<{ data: TResponse }> {
  try {
    return await request(payload)
  } catch (error) {
    if (!shouldRetryWithoutListenerMode(error, payload)) {
      throw error
    }

    const { listener_mode: _listenerMode, ...fallbackPayload } = payload
    return request(fallbackPayload)
  }
}

function shouldRetryWithoutListenerMode(
  error: unknown,
  payload: { listener_mode?: string | null },
): boolean {
  if (payload.listener_mode == null) return false

  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
  if (!Array.isArray(detail)) return false

  return detail.some((item) => {
    if (!item || typeof item !== 'object') return false

    const entry = item as { type?: string; loc?: unknown[] }
    return entry.type === 'extra_forbidden' && Array.isArray(entry.loc) && entry.loc.includes('listener_mode')
  })
}

function normalizeMailAccount(account: MailAccountItem): MailAccountItem {
  return {
    ...account,
    provider_label: account.provider_label || account.provider,
    auth_hint: account.auth_hint || '',
    supports_app_password: Boolean(account.supports_app_password),
    suggested_folders: Array.isArray(account.suggested_folders) ? account.suggested_folders : [],
    folders: Array.isArray(account.folders) ? account.folders : [],
    listener_mode: account.listener_mode || 'polling',
    graph_connected: Boolean(account.graph_connected),
  }
}
