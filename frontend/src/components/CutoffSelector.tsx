import React from 'react'

interface CutoffSelectorProps {
  cutoffHour: number
  cutoffMinute: number
  onChange: (hour: number, minute: number) => void
}

export function CutoffSelector({ cutoffHour, cutoffMinute, onChange }: CutoffSelectorProps) {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <label className="text-sm font-medium text-gray-700">Decision Cutoff (UTC, day-1):</label>
      <div className="flex items-center gap-1">
        <select
          value={cutoffHour}
          onChange={e => onChange(Number(e.target.value), cutoffMinute)}
          className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Cutoff hour"
        >
          {Array.from({ length: 24 }, (_, i) => (
            <option key={i} value={i}>{String(i).padStart(2, '0')}</option>
          ))}
        </select>
        <span className="text-gray-500">:</span>
        <select
          value={cutoffMinute}
          onChange={e => onChange(cutoffHour, Number(e.target.value))}
          className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Cutoff minute"
        >
          <option value={0}>00</option>
          <option value={30}>30</option>
        </select>
        <span className="text-xs text-gray-400 ml-1">UTC</span>
      </div>
      <span className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-2 py-0.5">
        Analytical assumption — not an official market deadline
      </span>
    </div>
  )
}
