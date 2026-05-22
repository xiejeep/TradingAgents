import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export interface AnalysisConfig {
  ticker: string
  analysis_date: string
  data_vendor: string
  output_language: string
  analysts: string[]
  research_depth: number
  llm_provider: string
  backend_url?: string
  shallow_thinker: string
  deep_thinker: string
  google_thinking_level?: string
  openai_reasoning_effort?: string
  anthropic_effort?: string
  checkpoint_enabled: boolean
}

export interface TaskCreated {
  task_id: string
}

export interface StreamMessage {
  type: string
  data?: Record<string, any>
  content?: string
}

export interface ReportData {
  task_id: string
  status: string
  decision?: string
  rating?: string
  report_path?: string
  market_report?: string
  sentiment_report?: string
  news_report?: string
  fundamentals_report?: string
  investment_plan?: string
  trader_investment_plan?: string
  final_trade_decision?: string
  error?: string
}

export interface HistoryEntry {
  id: string
  ticker: string
  analysis_date: string
  completed_at: string
  decision: string
  rating?: string
  report_path?: string
}

export interface HistoryListResponse {
  entries: HistoryEntry[]
  total: number
  limit: number
  offset: number
}

export interface HistoryDetailResponse {
  entry: HistoryEntry
  report_content: string | null
}

export interface KeyStatus {
  llm: Record<string, { env_var: string; masked: string | null; is_set: boolean }>
  data: Record<string, { env_var: string; masked: string | null; is_set: boolean }>
}

export interface ModelOption {
  provider: string
  models: { label: string; value: string }[]
}

export function createAnalysis(config: AnalysisConfig): Promise<TaskCreated> {
  return api.post('/analyze', config).then((r) => r.data)
}

export function getReport(taskId: string): Promise<ReportData> {
  return api.get(`/report/${taskId}`).then((r) => r.data)
}

export function getReportPdfUrl(taskId: string): string {
  return `/api/report/${taskId}/pdf`
}

export function getHistory(params: {
  ticker?: string
  limit?: number
  offset?: number
}): Promise<HistoryListResponse> {
  return api.get('/history', { params }).then((r) => r.data)
}

export function getHistoryDetail(entryId: string): Promise<HistoryDetailResponse> {
  return api.get(`/history/${entryId}`).then((r) => r.data)
}

export function getHistoryPdfUrl(entryId: string): string {
  return `/api/history/${entryId}/pdf`
}

export function getSettings(): Promise<KeyStatus> {
  return api.get('/settings').then((r) => r.data)
}

export function saveSettings(keys: Record<string, string>): Promise<void> {
  return api.post('/settings', { keys }).then((r) => r.data)
}

export function getModels(provider: string): Promise<ModelOption> {
  return api.get(`/models/${provider}`).then((r) => r.data)
}

export function getHealth(): Promise<{ status: string }> {
  return api.get('/health').then((r) => r.data)
}

export function createWebSocket(taskId: string): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  const host = window.location.host
  return new WebSocket(`${protocol}://${host}/ws/stream/${taskId}`)
}
