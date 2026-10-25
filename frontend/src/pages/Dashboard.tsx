import React, { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, BarChart, Bar
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { KpiCard } from '../components/KpiCard'
import { LoadingSpinner, ErrorState, EmptyState } from '../components/LoadingState'
import { useApi } from '../hooks/useApi'
import { getMetrics, getTimeseries, getDailyMetrics } from '../services/api'

interface DashboardProps {
  cutoffHour: number
  cutoffMinute: number
}

function fmt(v: number | null, dec = 0): string {
  if (v === null || v === undefined) return '—'
  return v.toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec })
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded shadow-lg p-3 text-xs max-w-xs">
      <p className="font-semibold text-gray-700 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {p.value === null ? '—' : `${Number(p.value).toFixed(0)} MW`}
        </p>
      ))}
    </div>
  )
}

export function Dashboard({ cutoffHour, cutoffMinute }: DashboardProps) {
  const metrics = useApi(() => getMetrics(cutoffHour, cutoffMinute), [cutoffHour, cutoffMinute])
  const timeseries = useApi(() => getTimeseries(cutoffHour, cutoffMinute), [cutoffHour, cutoffMinute])
  const daily = useApi(() => getDailyMetrics(cutoffHour, cutoffMinute), [cutoffHour, cutoffMinute])

  const chartData = useMemo(() => {
    if (!timeseries.data?.data) return []
    // Sample every 2 points for readability (1488 points is too dense)
    return timeseries.data.data
      .filter((_, i) => i % 2 === 0)
      .map(d => ({
        t: format(parseISO(d.delivery_start), 'dd MMM HH:mm'),
        actual: d.actual_generation,
        forecast: d.selected_forecast,
        error: d.signed_error,
      }))
  }, [timeseries.data])

  const dailyChartData = useMemo(() => {
    if (!daily.data) return []
    return daily.data.map(d => ({
      date: format(parseISO(d.date), 'dd MMM'),
      mae: d.mae,
      coverage: d.forecast_coverage_pct,
    }))
  }, [daily.data])

  if (metrics.loading) return <LoadingSpinner />
  if (metrics.error) return <ErrorState message={metrics.error} onRetry={metrics.reload} />
  const m = metrics.data

  if (!m || m.n_with_forecast === 0) {
    return <EmptyState message="No analysis data available for January 2026." />
  }

  return (
    <div className="space-y-6">
      {/* KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard
          title="MAE"
          value={fmt(m.mae, 0)}
          unit="MW"
          description={`Mean Absolute Error across ${m.n_with_forecast} intervals`}
        />
        <KpiCard
          title="RMSE"
          value={fmt(m.rmse, 0)}
          unit="MW"
          description="Root Mean Squared Error (penalises larger errors)"
        />
        <KpiCard
          title="Mean Bias"
          value={m.mean_bias_error !== null ? (m.mean_bias_error > 0 ? '+' : '') + fmt(m.mean_bias_error, 0) : null}
          unit="MW"
          description="Positive = systematic overforecast; negative = underforecast"
          highlight={m.mean_bias_error !== null ? (m.mean_bias_error > 0 ? 'negative' : 'positive') : 'neutral'}
        />
        <KpiCard
          title="Forecast Coverage"
          value={fmt(m.forecast_coverage_pct, 1)}
          unit="%"
          description={`${m.n_with_forecast} of ${m.total_intervals} intervals have an eligible day-ahead forecast`}
        />
        <KpiCard
          title="Mean Actual"
          value={fmt(m.mean_actual, 0)}
          unit="MW"
          description="Mean actual wind generation across comparable intervals"
        />
        <KpiCard
          title="Mean Forecast"
          value={fmt(m.mean_forecast, 0)}
          unit="MW"
          description="Mean selected day-ahead forecast across comparable intervals"
        />
      </div>

      {/* Actual vs Forecast Chart */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Actual vs Day-Ahead Forecast — January 2026</h2>
        <p className="text-xs text-gray-400 mb-4">Generation in MW (UTC). Gaps indicate missing data.</p>
        {timeseries.loading ? (
          <LoadingSpinner />
        ) : timeseries.error ? (
          <ErrorState message={timeseries.error} />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="t" tick={{ fontSize: 10 }} interval={47} />
              <YAxis tick={{ fontSize: 10 }} unit=" MW" width={72} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual (MW)"
                stroke="#2563eb"
                dot={false}
                strokeWidth={1.5}
                connectNulls={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                name="Day-Ahead Forecast (MW)"
                stroke="#f59e0b"
                dot={false}
                strokeWidth={1.5}
                strokeDasharray="4 2"
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Error time series */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Forecast Error — January 2026</h2>
        <p className="text-xs text-gray-400 mb-4">Signed error = forecast − actual (MW). Positive = overforecast.</p>
        {timeseries.loading ? (
          <LoadingSpinner />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="t" tick={{ fontSize: 10 }} interval={47} />
              <YAxis tick={{ fontSize: 10 }} unit=" MW" width={72} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
              <Line
                type="monotone"
                dataKey="error"
                name="Signed Error (MW)"
                stroke="#ef4444"
                dot={false}
                strokeWidth={1}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* Daily MAE */}
      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Daily MAE</h2>
          <p className="text-xs text-gray-400 mb-4">Mean absolute error per calendar day (MW).</p>
          {daily.loading ? <LoadingSpinner /> : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={dailyChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={6} />
                <YAxis tick={{ fontSize: 10 }} unit=" MW" width={64} />
                <Tooltip formatter={(v: number) => [`${v?.toFixed(0)} MW`, 'MAE']} />
                <Bar dataKey="mae" name="MAE" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-1">Directional Error</h2>
          <p className="text-xs text-gray-400 mb-3">Overforecast vs underforecast split.</p>
          {m && (
            <div className="space-y-3 mt-2">
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-32">Overforecast</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-amber-400 rounded-full transition-all"
                    style={{ width: `${m.overforecast_pct ?? 0}%` }}
                  />
                </div>
                <span className="text-xs font-mono w-12 text-right">{fmt(m.overforecast_pct, 1)}%</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-32">Underforecast</span>
                <div className="flex-1 bg-gray-100 rounded-full h-4 overflow-hidden">
                  <div
                    className="h-full bg-blue-400 rounded-full transition-all"
                    style={{ width: `${m.underforecast_pct ?? 0}%` }}
                  />
                </div>
                <span className="text-xs font-mono w-12 text-right">{fmt(m.underforecast_pct, 1)}%</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                WAPE: {fmt(m.wape, 2)}%
                {m.mape !== null && ` · MAPE: ${fmt(m.mape, 2)}%`}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
