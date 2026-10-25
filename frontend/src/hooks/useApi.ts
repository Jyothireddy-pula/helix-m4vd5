import { useState, useEffect, useCallback } from 'react'

export interface ApiState<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

export function useApi<T>(fetcher: () => Promise<T>, deps: unknown[]): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rev, setRev] = useState(0)

  const reload = useCallback(() => setRev(r => r + 1), [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetcher()
      .then(d => { if (!cancelled) { setData(d); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.message || 'Error'); setLoading(false) } })
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, rev])

  return { data, loading, error, reload }
}
