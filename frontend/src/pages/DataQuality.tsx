import React from 'react'
import { format, parseISO } from 'date-fns'
import { useApi } from '../hooks/useApi'
import { getQuality } from '../services/api'
import { LoadingSpinner, ErrorState } from '../components/LoadingState'

export function DataQuality() {
  const quality = useApi(() => getQuality(), [])
  const q = quality.data

  const fmtTs = (s: string | null) => {
    if (!s) return '—'
    try { return format(parseISO(s), 'dd MMM yyyy HH:mm') + ' UTC' } catch { return s }
  }

  if (quality.loading) return <LoadingSpinner />
  if (quality.error) return <ErrorState message={quality.error} onRetry={quality.reload} />
  if (!q) return null

  const coveragePct = q.expected_intervals > 0
    ? ((q.actual_intervals_retrieved / q.expected_intervals) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="space-y-5">
      {/* Coverage overview */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Data Coverage</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Stat label="Expected Intervals" value={q.expected_intervals.toLocaleString()} />
          <Stat label="Actuals Retrieved" value={q.actual_intervals_retrieved.toLocaleString()} sub={`${coveragePct}% coverage`} />
          <Stat label="Missing Actuals" value={q.missing_actual_intervals.toLocaleString()} warn={q.missing_actual_intervals > 0} />
          <Stat label="Forecast Records" value={q.forecast_records.toLocaleString()} />
        </div>
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs text-gray-500">Actual coverage</span>
            <span className="text-xs font-mono text-gray-700">{coveragePct}%</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div
              className="h-3 rounded-full bg-blue-500 transition-all"
              style={{ width: `${Math.min(100, parseFloat(coveragePct))}%` }}
            />
          </div>
        </div>
      </div>

      {/* Ingestion history */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Ingestion History</h2>
        {q.last_ingestion_runs.length === 0 ? (
          <p className="text-sm text-gray-400">No ingestion runs found. Run <code className="bg-gray-100 px-1 rounded">python ingest.py</code> to load data.</p>
        ) : (
          <table className="w-full text-xs">
            <thead className="text-gray-500 uppercase tracking-wide border-b border-gray-100">
              <tr>
                <th className="pb-2 text-left">Dataset</th>
                <th className="pb-2 text-left">Status</th>
                <th className="pb-2 text-left">Finished</th>
                <th className="pb-2 text-right">Records Inserted</th>
              </tr>
            </thead>
            <tbody>
              {q.last_ingestion_runs.map((r, i) => (
                <tr key={i} className="border-t border-gray-50">
                  <td className="py-1.5 font-mono">{r.dataset}</td>
                  <td className="py-1.5">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${r.status === 'success' ? 'bg-green-100 text-green-700' : r.status === 'running' ? 'bg-blue-100 text-blue-700' : 'bg-red-100 text-red-600'}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="py-1.5 text-gray-500">{fmtTs(r.finished_at)}</td>
                  <td className="py-1.5 text-right font-mono">{r.records_inserted?.toLocaleString() ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Provenance */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Data Provenance</h2>
        <dl className="space-y-3 text-sm">
          <Row label="Actual Generation Source" value={q.sources.actuals.dataset} />
          <Row label="Actuals URL" value={<a href={q.sources.actuals.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline break-all">{q.sources.actuals.url}</a>} />
          <Row label="Forecast Source" value={q.sources.forecasts.dataset} />
          <Row label="Forecasts URL" value={<a href={q.sources.forecasts.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline break-all">{q.sources.forecasts.url}</a>} />
          <Row label="Unit" value={q.sources.actuals.unit} />
          <Row label="Timezone" value={q.timezone} />
          <Row label="Earliest Forecast Publish" value={fmtTs(q.earliest_publish_time)} />
          <Row label="Latest Forecast Publish" value={fmtTs(q.latest_publish_time)} />
          <Row label="Analysis Period" value="1 January 2026 – 31 January 2026 (UTC)" />
          <Row label="Decision Cutoff" value={q.decision_cutoff_assumption} />
        </dl>
      </div>

      {/* Metric definitions */}
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Metric Definitions</h2>
        <dl className="space-y-2 text-xs text-gray-600">
          <div><dt className="font-semibold">Error Convention</dt><dd className="ml-4">signed_error = forecast − actual. Positive → overforecast, Negative → underforecast.</dd></div>
          <div><dt className="font-semibold">MAE</dt><dd className="ml-4">Mean Absolute Error = mean of |forecast − actual|. Lower is better.</dd></div>
          <div><dt className="font-semibold">RMSE</dt><dd className="ml-4">Root Mean Squared Error = √(mean of (forecast − actual)²). Penalises large errors more than MAE.</dd></div>
          <div><dt className="font-semibold">Mean Bias Error</dt><dd className="ml-4">Mean of signed errors. Positive indicates systematic overforecast; negative indicates systematic underforecast.</dd></div>
          <div><dt className="font-semibold">WAPE</dt><dd className="ml-4">Weighted Absolute Percentage Error = sum(|error|) / sum(|actual|) × 100. Only calculated when sum(actual) &gt; 0.</dd></div>
          <div><dt className="font-semibold">MAPE</dt><dd className="ml-4">Mean Absolute Percentage Error = mean of |error/actual| × 100. Only calculated for non-zero actuals; undefined otherwise.</dd></div>
        </dl>
      </div>
    </div>
  )
}

function Stat({ label, value, sub, warn }: { label: string; value: string; sub?: string; warn?: boolean }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className={`text-lg font-bold ${warn ? 'text-amber-600' : 'text-gray-800'}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col sm:flex-row sm:gap-4">
      <dt className="text-gray-500 sm:w-48 flex-shrink-0">{label}</dt>
      <dd className="text-gray-800">{value}</dd>
    </div>
  )
}
