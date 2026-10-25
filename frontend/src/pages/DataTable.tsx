import React, { useState, useMemo } from 'react'
import { format, parseISO } from 'date-fns'
import { useApi } from '../hooks/useApi'
import { getTimeseries, getExportUrl } from '../services/api'
import { LoadingSpinner, ErrorState, EmptyState } from '../components/LoadingState'
import type { TimeseriesPoint } from '../types/api'

interface DataTableProps {
  cutoffHour: number
  cutoffMinute: number
}

const PAGE_SIZE = 50

type SortKey = keyof TimeseriesPoint
type SortDir = 'asc' | 'desc'

export function DataTable({ cutoffHour, cutoffMinute }: DataTableProps) {
  const ts = useApi(() => getTimeseries(cutoffHour, cutoffMinute), [cutoffHour, cutoffMinute])
  const [page, setPage] = useState(0)
  const [sortKey, setSortKey] = useState<SortKey>('delivery_start')
  const [sortDir, setSortDir] = useState<SortDir>('asc')
  const [search, setSearch] = useState('')

  const sorted = useMemo(() => {
    if (!ts.data?.data) return []
    let rows = [...ts.data.data]
    if (search) {
      rows = rows.filter(r =>
        r.delivery_start.includes(search) ||
        r.forecast_status.includes(search) ||
        (r.data_quality_flag && r.data_quality_flag.includes(search))
      )
    }
    rows.sort((a, b) => {
      const av = a[sortKey] as any
      const bv = b[sortKey] as any
      if (av === null) return 1
      if (bv === null) return -1
      return sortDir === 'asc' ? (av < bv ? -1 : 1) : (av > bv ? -1 : 1)
    })
    return rows
  }, [ts.data, sortKey, sortDir, search])

  const pageData = useMemo(() => sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE), [sorted, page])
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('asc') }
    setPage(0)
  }

  const fmtDt = (s: string) => format(parseISO(s), 'dd MMM HH:mm') + ' UTC'
  const fmtN = (v: number | null, d = 0) => v === null ? '—' : v.toFixed(d)

  if (ts.loading) return <LoadingSpinner />
  if (ts.error) return <ErrorState message={ts.error} onRetry={ts.reload} />
  if (!ts.data?.data?.length) return <EmptyState message="No data. Run ingestion first." />

  const Th = ({ col, label }: { col: SortKey; label: string }) => (
    <th
      className="px-3 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide cursor-pointer hover:text-gray-800 select-none whitespace-nowrap"
      onClick={() => handleSort(col)}
    >
      {label} {sortKey === col ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-3 items-center justify-between">
        <input
          type="search"
          placeholder="Search date, status, flag…"
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
          className="border border-gray-300 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Search table"
        />
        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-500">{sorted.length.toLocaleString()} rows</span>
          <a
            href={getExportUrl(cutoffHour, cutoffMinute)}
            download="wind_forecast_analysis.csv"
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Export CSV
          </a>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <Th col="delivery_start" label="Delivery (UTC)" />
                <Th col="actual_generation" label="Actual (MW)" />
                <Th col="selected_forecast" label="Forecast (MW)" />
                <Th col="forecast_publish_time" label="Pub. Time (UTC)" />
                <Th col="signed_error" label="Signed Error" />
                <Th col="abs_error" label="Abs Error" />
                <Th col="lead_time_hours" label="Lead Time" />
                <Th col="forecast_status" label="Status" />
              </tr>
            </thead>
            <tbody>
              {pageData.map((row, i) => (
                <tr key={i} className="border-t border-gray-50 hover:bg-gray-50">
                  <td className="px-3 py-1.5 font-mono whitespace-nowrap">{fmtDt(row.delivery_start)}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{fmtN(row.actual_generation, 0)}</td>
                  <td className="px-3 py-1.5 text-right font-mono">{fmtN(row.selected_forecast, 0)}</td>
                  <td className="px-3 py-1.5 font-mono whitespace-nowrap text-gray-500">{row.forecast_publish_time ? fmtDt(row.forecast_publish_time) : '—'}</td>
                  <td className={`px-3 py-1.5 text-right font-mono ${row.signed_error !== null ? (row.signed_error > 0 ? 'text-amber-600' : row.signed_error < 0 ? 'text-blue-600' : '') : ''}`}>
                    {row.signed_error !== null ? (row.signed_error > 0 ? '+' : '') + fmtN(row.signed_error, 0) : '—'}
                  </td>
                  <td className="px-3 py-1.5 text-right font-mono">{fmtN(row.abs_error, 0)}</td>
                  <td className="px-3 py-1.5 text-right">{row.lead_time_hours !== null ? `${row.lead_time_hours.toFixed(1)}h` : '—'}</td>
                  <td className="px-3 py-1.5">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${row.forecast_status === 'available' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>
                      {row.forecast_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center gap-2 justify-center">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page + 1} of {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page === totalPages - 1}
            className="px-3 py-1 border rounded text-sm disabled:opacity-40 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
