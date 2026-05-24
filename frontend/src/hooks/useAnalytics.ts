import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchFormSettings, fetchMetrics } from '../api/client'
import type { CohortFilters, FormSettings, MetricsResponse } from '../types'

const DEFAULT_DISEASE = 'Multiple Myeloma'

export function useAnalytics() {
  const [filters, setFilters] = useState<CohortFilters>({ disease: DEFAULT_DISEASE })
  const [settings, setSettings] = useState<FormSettings | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Load form settings when disease changes
  useEffect(() => {
    const disease = filters.disease ?? DEFAULT_DISEASE
    fetchFormSettings(disease).then(setSettings).catch(() => {})
  }, [filters.disease])

  // Debounce metrics fetch when filters change
  const loadMetrics = useCallback((f: CohortFilters) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await fetchMetrics(f)
        setMetrics(data)
      } catch {
        setError('Failed to load analytics data.')
      } finally {
        setLoading(false)
      }
    }, 400)
  }, [])

  useEffect(() => {
    loadMetrics(filters)
  }, [filters, loadMetrics])

  const updateFilter = useCallback(<K extends keyof CohortFilters>(key: K, value: CohortFilters[K]) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({ disease: filters.disease ?? DEFAULT_DISEASE })
  }, [filters.disease])

  return { filters, settings, metrics, loading, error, updateFilter, clearFilters, setFilters }
}
