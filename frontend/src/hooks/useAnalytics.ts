import { useState, useEffect, useCallback, useRef } from 'react'
import { fetchFormSettings, fetchMetrics } from '../api/client'
import type { CohortFilters, FormSettings, MetricsResponse } from '../types'

const DEFAULT_DISEASE = 'Multiple Myeloma'

const DISEASE_SPECIFIC_FIELDS: Partial<CohortFilters> = {
  stage: undefined,
  cytogenetic_markers: undefined,
  high_risk_cytogenetics: undefined,
  tp53_disruption: undefined,
  refractory_status: undefined,
  has_sct: undefined,
  meets_crab: undefined,
  has_bone_lesions: undefined,
  plasma_cell_leukemia: undefined,
  mrd_status: undefined,
  er_status: undefined,
  her2_status: undefined,
  tnbc_status: undefined,
}

export function useAnalytics() {
  const [filters, setFilters] = useState<CohortFilters>({ disease: DEFAULT_DISEASE })
  const [settings, setSettings] = useState<FormSettings | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const prevOrgRef = useRef<string | undefined>(undefined)

  // Load form settings when disease or org changes
  useEffect(() => {
    let cancelled = false
    const disease = filters.disease ?? DEFAULT_DISEASE
    fetchFormSettings(disease, filters.org)
      .then(s => { if (!cancelled) setSettings(s) })
      .catch(err => { if (!cancelled) console.error('Failed to load form settings', err) })
    return () => { cancelled = true }
  }, [filters.disease, filters.org])

  // Auto-select the disease with the most patients when org changes
  useEffect(() => {
    const org = filters.org
    if (org === prevOrgRef.current) return
    prevOrgRef.current = org
    if (!org) return  // org cleared — don't change disease

    fetchFormSettings(DEFAULT_DISEASE, org).then(s => {
      const topDisease = s.diseases[0]  // backend already sorts by count desc
      if (!topDisease) return
      setFilters(prev => ({ ...prev, ...DISEASE_SPECIFIC_FIELDS, disease: topDisease }))
    }).catch((err) => {
      console.error('Failed to load form settings for org auto-select', err)
    })
  }, [filters.org])

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
