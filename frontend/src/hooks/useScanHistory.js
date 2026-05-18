import { useCallback, useEffect, useState } from 'react'
import { scanApi } from '../services/api'

export function useScanHistory(limit = 25) {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const response = await scanApi.history(limit)
      setHistory(response.data)
    } catch (apiError) {
      setError(apiError.response?.data?.detail || 'Unable to load scan history. Sign in and ensure the backend is running.')
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    let ignore = false

    async function loadInitialHistory() {
      try {
        const response = await scanApi.history(limit)
        if (!ignore) {
          setHistory(response.data)
        }
      } catch (apiError) {
        if (!ignore) {
          setError(apiError.response?.data?.detail || 'Unable to load scan history. Sign in and ensure the backend is running.')
        }
      } finally {
        if (!ignore) {
          setLoading(false)
        }
      }
    }

    loadInitialHistory()

    return () => {
      ignore = true
    }
  }, [limit])

  return { history, loading, error, refresh }
}
