const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')

export type ComparisonRow = {
  startTime: string
  publishTime: string | null
  forecast_mw: number | null
  actual_mw: number | null
  error_mw: number | null
  status: string
}
export type Metrics = {
  matched_intervals: number
  intervals_returned: number
  coverage_pct: number
  mae_mw: number | null
  rmse_mw: number | null
  bias_mw: number | null
}
export type ComparisonResponse = {
  delivery_date: string
  decision_cutoff: string
  cutoff_hour_uk: number
  records: ComparisonRow[]
  metrics: Metrics
  note: string
  source: string
}
export async function getComparison(date: string, cutoffHour: number): Promise<ComparisonResponse> {
  const params = new URLSearchParams({ delivery_date: date, cutoff_hour: String(cutoffHour) })
  const response = await fetch(`${API_BASE}/api/comparison?${params}`)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || `API request failed (${response.status})`)
  }
  return response.json()
}
