import { useState, useEffect } from 'react'
import { fetchSavedCohorts, deleteSavedCohort } from '../../api/client'
import type { CohortFilters, SavedCohort } from '../../types'

interface Props {
  onLoad: (filters: CohortFilters, cohortId: number) => void
  refreshToken: number
}

export default function SavedCohortsList({ onLoad, refreshToken }: Props) {
  const [cohorts, setCohorts] = useState<SavedCohort[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    fetchSavedCohorts()
      .then(setCohorts)
      .catch(() => setCohorts([]))
      .finally(() => setLoading(false))
  }, [refreshToken])

  async function handleDelete(id: number) {
    await deleteSavedCohort(id)
    setCohorts(prev => prev.filter(c => c.id !== id))
  }

  if (loading) {
    return <p className="text-xs text-slate-500 italic py-2">Loading…</p>
  }

  if (cohorts.length === 0) {
    return <p className="text-xs text-slate-500 italic py-2">No saved cohorts yet.</p>
  }

  return (
    <div className="space-y-1.5">
      {cohorts.map(c => (
        <div key={c.id} className="bg-slate-700/50 rounded px-2 py-1.5 group">
          <div className="flex items-start justify-between gap-1">
            <button
              onClick={() => onLoad(c.filters, c.id)}
              className="text-xs text-teal-400 hover:text-teal-300 font-medium text-left leading-tight truncate flex-1"
              title={c.description || c.name}
            >
              {c.name}
            </button>
            <button
              onClick={() => handleDelete(c.id)}
              className="text-slate-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              title="Delete"
            >
              ✕
            </button>
          </div>
          {c.description && (
            <p className="text-xs text-slate-500 mt-0.5 truncate">{c.description}</p>
          )}
        </div>
      ))}
    </div>
  )
}
