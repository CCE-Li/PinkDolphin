export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  username: string
  token_type: string
}

export interface ChangePasswordRequest {
  current_username: string
  current_password: string
  new_username: string
  new_password: string
}

export interface EnvFileItem {
  path: string
  content: string
  editable_keys: string[]
}

export interface DashboardSummary {
  total_emails: number
  analyzed_emails: number
  open_incidents: number
  critical_emails: number
  high_risk_emails: number
  monitored_mailboxes: number
  listening_mailboxes: number
  mailbox_errors: number
}

export interface EmailListItem {
  id: string
  created_at: string
  updated_at: string
  message_id: string | null
  subject: string | null
  source: string
  status: string
  mailbox_account_id: string | null
  mailbox_display_name: string | null
  mailbox_email_address: string | null
  remote_uid: number | null
  latest_risk_level: string | null
  latest_score: number | null
  latest_recommended_action: string | null
}

export interface EmailAddressItem {
  id: string
  display_name: string | null
  address: string
  role: string
}

export interface UrlItem {
  id: string
  url: string
  domain: string | null
  path: string | null
  is_shortened: boolean
}

export interface AttachmentItem {
  id: string
  filename: string | null
  content_type: string | null
  size: number
  sha256: string | null
}

export interface AnalyzerResultItem {
  id: string
  created_at: string
  updated_at: string
  analysis_result_id: string
  analyzer_name: string
  enabled: boolean
  status: string
  score: number
  severity: string
  summary: string
  signals: string[]
  evidence: Record<string, unknown>
}

export interface AnalysisResultItem {
  id: string
  created_at: string
  updated_at: string
  email_id: string
  total_score: number
  risk_level: string
  recommended_action: string
  summary: string
  override_reason: string | null
  decision_details: Record<string, unknown>
  analyzer_results: AnalyzerResultItem[]
}

export interface EmailDetail {
  id: string
  created_at: string
  updated_at: string
  message_id: string | null
  subject: string | null
  authentication_results: string | null
  send_time: string | null
  raw_headers: Record<string, unknown>
  raw_email: string | null
  body_text: string | null
  body_html: string | null
  source: string
  status: string
  latest_risk_level: string | null
  latest_score: number | null
  addresses: EmailAddressItem[]
  attachments: AttachmentItem[]
  urls: UrlItem[]
  analysis_results: AnalysisResultItem[]
}

export interface EmailActionRequest {
  action_type: string
  reason?: string
  actor: string
  metadata_json: Record<string, unknown>
}

export interface EmailAnalyzeResponse {
  email_id: string
  analysis_id: string
  risk_level: string
  recommended_action: string
  total_score: number
  analyzer_results: AnalyzerResultItem[]
}

export interface EmailAnalyzeDeferredResponse {
  email_id: string
  status: string
  message: string
  component: string
}

export interface RuleItem {
  id: string
  created_at: string
  updated_at: string
  name: string
  description: string | null
  is_active: boolean
  condition_type: string
  condition_value: string
  score_modifier: number
  severity: string
  override_action: string | null
}

export interface RulePayload {
  name: string
  description?: string | null
  is_active: boolean
  condition_type: string
  condition_value: string
  score_modifier: number
  severity: string
  override_action?: string | null
}

export interface AuditLogItem {
  id: string
  created_at: string
  updated_at: string
  event_type: string
  actor: string
  resource_type: string
  resource_id: string
  details: Record<string, unknown>
  message: string
}

export interface IncidentItem {
  id: string
  created_at: string
  updated_at: string
  email_id: string
  analysis_result_id: string | null
  title: string
  description: string | null
  status: string
  risk_level: string
}

export interface MailAccountItem {
  id: string
  created_at: string
  updated_at: string
  owner_email: string
  email_address: string
  display_name: string | null
  provider: string
  imap_host: string
  imap_port: number
  imap_username: string
  mailbox_folder: string
  use_ssl: boolean
  is_active: boolean
  status: string
  listen_interval_seconds: number
  last_seen_uid: number | null
  last_synced_uid: number | null
  last_sync_at: string | null
  last_error: string | null
}

export interface MailAccountPayload {
  owner_email?: string | null
  email_address: string
  display_name?: string | null
  provider: string
  imap_host?: string | null
  imap_port?: number | null
  imap_username?: string | null
  imap_password?: string
  mailbox_folder: string
  use_ssl: boolean
  is_active: boolean
  listen_interval_seconds?: number | null
}

export interface MailAccountTestResult {
  ok: boolean
  message: string
  mailbox_exists: boolean
  highest_uid: number | null
}

export interface MailAccountSyncResult {
  account_id: string
  queued: number
  synced: number
  highest_uid: number | null
}

export interface AllowlistItem {
  id: string
  created_at: string
  updated_at: string
  list_type: string
  value: string
  is_active: boolean
  skip_url_scan: boolean
  skip_attachment_scan: boolean
  skip_llm_scan: boolean
}

export interface AllowlistPayload {
  list_type: string
  value: string
  is_active: boolean
  skip_url_scan: boolean
  skip_attachment_scan: boolean
  skip_llm_scan: boolean
}

export interface IssueLogItem {
  id: string
  created_at: string
  updated_at: string
  component: string
  severity: string
  message: string
  details: Record<string, unknown>
}
