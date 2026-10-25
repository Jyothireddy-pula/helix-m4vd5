import React, { useState } from 'react'
import { format, parseISO } from 'date-fns'
import { useApi } from '../hooks/useApi'
import { getVintages } from '../services/api'
import { LoadingSpinner, ErrorState } from '../components/LoadingState'

interface VintageExplorerProps {
  cutoffHour: number
  cutoffMinute: number
}

export function VintageExplorer({ cutoffHour, cutoffMinute }: VintageExplorerProps) {
  const [selectedDate, setSelectedDate] = useState('2026-01-15')
  const [selectedHour, setSelectedHour] = useState(12)
  const [queryTs, setQueryTs] = useState<string | null>(null)

  const deliveryStart = `${selectedDate}T${String(selectedHour).padStart(2, '0')}:00:00Z`

  const vintages = useApi(
    () => queryTs ? getVintages(queryTs, cutoffHour, cutoffMinute) : Promise.resolve(null as any),
    [queryTs, cutoffHour, cutoffMinute]
  )

  function handleSearch() {
    setQueryTs(deliveryStart)
  }

  const fmt = (v: number | null) => v === null ? '—' : v.toLocaleString(undefined, { maximumFractionDigits: 0 }) + ' MW'
  const fmtTs = (s: string | null) => s ? format(parseISO(s), 'dd MMM yyyy HH:mm') + ' UTC' : '—'
  const fmtHours = (h: number | null) => h === null ? '—' : `${h.toFixed(1)}h`

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
        <h2 className="text-sm font-semibold text-gray-700 mb-1">Forecast Vintage Explorer</h2>
        <p className="text-xs text-gray-500 mb-4">
          Select a delivery interval to see all available forecast vintages, which was eligible at the day-ahead cutoff, and why.
        </p>
        <div className="flex gap-3 flex-wrap items-end">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Delivery Date</label>
            <input
              type="date"
              value={selectedDate}
              min="2026-01-01"
              max="2026-01-31"
              onChange={e => setSelectedDate(e.target.value)}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Delivery Hour (UTC)</label>
            <select
              value={selectedHour}
              onChange={e => setSelectedHour(Number(e.target.value))}
              className="border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Array.from({ length: 24 }, (_, i) => (
                <option key={i} value={i}>{String(i).padStart(2, '0')}:00 UTC</option>
              ))}
            </select>
          </div>
          <button
            onClick={handleSearch}
            className="px-4 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Search
          </button>
        </div>
      </div>

      {!queryTs && (
        <div className="text-center text-gray-400 py-12 text-sm">Select a delivery interval and click Search to explore forecast vintages.</div>
      )}

      {queryTs && vintages.loading && <LoadingSpinner />}
      {queryTs && vintages.error && <ErrorState message={vintages.error} />}
      {queryTs && vintages.data && (() => {
        const v = vintages.data
        return (
          <div className="space-y-4">
            {/* Summary card */}
            <div className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Delivery Interval: {fmtTs(v.delivery_start)}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-xs text-gray-500">Actual Generation</p>
                  <p className="font-semibold">{fmt(v.actual_generation)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Decision Cutoff</p>
                  <p className="font-semibold">{fmtTs(v.decision_cutoff)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Selected Forecast</p>
                  <p className="font-semibold text-amber-600">{fmt(v.selected_forecast)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Lead Time</p>
                  <p className="font-semibold">{fmtHours(v.lead_time_hours)}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Signed Error</p>
                  <p className={`font-semibold ${v.signed_error !== null ? (v.signed_error > 0 ? 'text-amber-600' : 'text-blue-600') : 'text-gray-400'}`}>
                    {v.signed_error !== null ? (v.signed_error > 0 ? '+' : '') + v.signed_error.toFixed(0) + ' MW' : '—'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Status</p>
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${v.forecast_status === 'available' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                    {v.forecast_status}
                  </span>
                </div>
              </div>
              {v.forecast_status === 'available' && (
                <p className="text-xs text-gray-500 mt-3 bg-blue-50 rounded p-2">
                  The selected forecast was published at <strong>{fmtTs(v.selected_publish_time)}</strong>,
                  which is before the decision cutoff ({fmtTs(v.decision_cutoff)}).
                  It had the latest publish time of all eligible vintages.
                </p>
              )}
            </div>

            {/* All vintages table */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100">
                <h3 className="text-sm font-semibold text-gray-700">
                  All Forecast Vintages ({v.vintages.length})
                </h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  Green rows are eligible (published before cutoff). The bold row is the one selected.
                </p>
              </div>
              {v.vintages.length === 0 ? (
                <div className="p-6 text-center text-gray-400 text-sm">No forecast vintages found for this interval.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead className="bg-gray-50 text-gray-500 uppercase tracking-wide">
                      <tr>
                        <th className="px-4 py-2 text-left">Publish Time (UTC)</th>
                        <th className="px-4 py-2 text-right">Forecast (MW)</th>
                        <th className="px-4 py-2 text-center">Eligible</th>
                        <th className="px-4 py-2 text-center">Selected</th>
                      </tr>
                    </thead>
                    <tbody>
                      {v.vintages.map((row: import('../types/api').Vintage, i: number) => {
                        const isSelected = row.publish_time_utc === v.selected_publish_time
                        return (
                          <tr
                            key={i}
                            className={`border-t border-gray-50 ${isSelected ? 'bg-amber-50 font-semibold' : row.eligible ? 'bg-green-50' : 'bg-red-50'}`}
                          >
                            <td className="px-4 py-1.5">{fmtTs(row.publish_time_utc)}</td>
                            <td className="px-4 py-1.5 text-right font-mono">{row.generation.toFixed(0)}</td>
                            <td className="px-4 py-1.5 text-center">
                              <span className={`px-1.5 py-0.5 rounded text-xs ${row.eligible ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                                {row.eligible ? '✓ Yes' : '✗ No'}
                              </span>
                            </td>
                            <td className="px-4 py-1.5 text-center">
                              {isSelected ? <span className="text-amber-600 font-bold">★ Selected</span> : null}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}
