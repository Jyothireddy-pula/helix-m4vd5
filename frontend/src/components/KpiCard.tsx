import React from 'react'

interface KpiCardProps {
  title: string
  value: string | number | null
  unit?: string
  description: string
  note?: string
  highlight?: 'positive' | 'negative' | 'neutral'
}

export function KpiCard({ title, value, unit, description, note, highlight }: KpiCardProps) {
  const colorClass = highlight === 'positive'
    ? 'text-green-600'
    : highlight === 'negative'
    ? 'text-red-600'
    : 'text-blue-700'

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5 flex flex-col gap-1 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{title}</p>
      <div className="flex items-baseline gap-1 mt-1">
        {value === null || value === undefined ? (
          <span className="text-2xl font-bold text-gray-400">—</span>
        ) : (
          <>
            <span className={`text-2xl font-bold ${colorClass}`}>{value}</span>
            {unit && <span className="text-sm text-gray-500">{unit}</span>}
          </>
        )}
      </div>
      <p className="text-xs text-gray-500 leading-snug mt-1">{description}</p>
      {note && <p className="text-xs text-amber-600 mt-1">{note}</p>}
    </div>
  )
}
