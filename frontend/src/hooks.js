import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from './api/client'

// Load data from an API function with loading / error state and a reload callback.
export function useApi(fn, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const load = useCallback(async (silent = false) => {
    if (!silent) setLoading(true)
    setError(null)
    try {
      const d = await fn()
      setData(d)
      return d
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setLoading(false)
    }
  }, deps)
  useEffect(() => { load() }, [load])
  return { data, setData, loading, error, reload: load }
}
