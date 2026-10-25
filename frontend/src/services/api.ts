import type { Metrics, TimeseriesPoint, DailyMetrics, LeadTimeMetrics, VintageResponse, DataQuality } from '../types/api'

const BASE = import.meta.env.VITE_API_URL || ''

async function fetchJson<T>(path: string, params?: Record<string, string | number>): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin)
  if (params) {
    Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, String(v)))
  }
  const res = await fetch(url.toString())
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText)
    throw new Error(`API ${res.status}: ${err}`)
  }
  return res.json()
}

export function getMetrics(cutoffHour: number, cutoffMinute: number): Promise<Metrics> {
  return fetchJson('/api/v1/analysis/metrics', { cutoff_hour: cutoffHour, cutoff_minute: cutoffMinute })
}

export function getTimeseries(cutoffHour: number, cutoffMinute: number): Promise<{ data: TimeseriesPoint[]; count: number }> {
  return fetchJson('/api/v1/analysis/timeseries', { cutoff_hour: cutoffHour, cutoff_minute: cutoffMinute })
}

export function getDailyMetrics(cutoffHour: number, cutoffMinute: number): Promise<DailyMetrics[]> {
  return fetchJson('/api/v1/analysis/daily', { cutoff_hour: cutoffHour, cutoff_minute: cutoffMinute })
}

export function getLeadTimeMetrics(cutoffHour: number, cutoffMinute: number): Promise<LeadTimeMetrics[]> {
  return fetchJson('/api/v1/analysis/lead-times', { cutoff_hour: cutoffHour, cutoff_minute: cutoffMinute })
}

export function getVintages(deliveryStart: string, cutoffHour: number, cutoffMinute: number): Promise<VintageResponse> {
  return fetchJson('/api/v1/forecasts/vintages', {
    delivery_start: deliveryStart,
    cutoff_hour: cutoffHour,
    cutoff_minute: cutoffMinute,
  })
}

export function getQuality(): Promise<DataQuality> {
  return fetchJson('/api/v1/quality')
}

export function getExportUrl(cutoffHour: number, cutoffMinute: number): string {
  return `${BASE}/api/v1/analysis/export.csv?cutoff_hour=${cutoffHour}&cutoff_minute=${cutoffMinute}`
}
