import { useCallback, useState } from 'react'
import { scanApi } from '../services/api'

function getApiError(error) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (detail?.message) {
    return detail.error ? `${detail.message} ${detail.error}` : detail.message
  }

  if (Array.isArray(detail) && detail[0]?.msg) {
    return detail[0].msg
  }

  if (!error.response) {
    return 'Cannot reach the API. Start the stack: docker compose up --build (or run uvicorn + redis + celery locally).'
  }

  return 'Unable to run scan. Check the backend and Nmap installation.'
}

export function useScan() {
  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const runScan = useCallback(async (target) => {
    setLoading(true)
    setError('')

    try {
      const response = await scanApi.run(target)
      let currentScan = response.data
      setScan(currentScan)

      const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

      while (['queued', 'running'].includes(currentScan.status)) {
        await wait(2500)
        const statusResponse = await scanApi.getById(currentScan.id)
        currentScan = statusResponse.data
        setScan(currentScan)
      }

      // Intel enrichment is saved after Nmap; poll getById (same payload, no extra rate limit).
      if (currentScan.status === 'completed') {
        for (let attempt = 0; attempt < 10; attempt += 1) {
          if (currentScan.open_ports_enriched != null) {
            break
          }
          await wait(2000)
          try {
            const statusResponse = await scanApi.getById(currentScan.id)
            currentScan = statusResponse.data
            setScan(currentScan)
          } catch {
            break
          }
        }
      }

      return currentScan
    } catch (apiError) {
      const message = getApiError(apiError)
      setError(message)
      throw apiError
    } finally {
      setLoading(false)
    }
  }, [])

  return { scan, loading, error, runScan, setScan }
}
