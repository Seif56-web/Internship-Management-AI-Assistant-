import { useState, useEffect, useCallback } from 'react'
import { getStagiaires } from '../services/stagiaires'

export function useStagiaires(params = {}) {
  const [stagiaires, setStagiaires] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getStagiaires(params)
      setStagiaires(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }, [JSON.stringify(params)])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { stagiaires, loading, error, refetch: fetch }
}
