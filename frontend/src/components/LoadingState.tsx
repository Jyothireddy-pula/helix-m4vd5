import React from 'react'

export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 gap-4 text-center">
      <div className="text-red-500 text-4xl">⚠</div>
      <p className="text-gray-700 font-medium">Failed to load data</p>
      <p className="text-sm text-gray-500 max-w-md">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Retry
        </button>
      )}
    </div>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 gap-2 text-center">
      <div className="text-gray-300 text-5xl">📭</div>
      <p className="text-gray-500">{message}</p>
      <p className="text-xs text-gray-400">Run the ingestion script to load January 2026 data.</p>
    </div>
  )
}

export function SkeletonRow() {
  return (
    <div className="flex gap-4 animate-pulse">
      <div className="h-4 bg-gray-200 rounded flex-1" />
      <div className="h-4 bg-gray-200 rounded w-24" />
      <div className="h-4 bg-gray-200 rounded w-24" />
    </div>
  )
}
