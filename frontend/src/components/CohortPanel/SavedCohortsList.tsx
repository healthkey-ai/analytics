import { useState, useEffect, useRef } from 'react'
import { fetchSavedCohorts, deleteSavedCohort, updateSavedCohort } from '../../api/client'
import type { CohortFilters, SavedCohort } from '../../types'

interface Props {
  onLoad: (filters: CohortFilters, cohortId: number, cohortName: string) => void
  refreshToken: number
}

export default function SavedCohortsList({ onLoad, refreshToken }: Props) {
  const [cohorts, setCohorts] = useState<SavedCohort[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingName, setEditingName] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetchSavedCohorts()
      .then(setCohorts)
      .catch((err) => {
        setError(err?.response?.status === 401 ? 'Session expired. Please log in again.' : 'Failed to load saved cohorts.')
        setCohorts([])
      })
      .finally(() => setLoading(false))
  }, [refreshToken])

  useEffect(() => {
    if (editingId !== null) inputRef.current?.focus()
  }, [editingId])

  function startEdit(c: SavedCohort) {
    setEditingId(c.id)
    setEditingName(c.name)
  }

  async function commitRename(id: number) {
    const trimmed = editingName.trim()
    setEditingId(null)
    if (!trimmed) return
    const original = cohorts.find(c => c.id === id)
    if (trimmed === original?.name) return
    try {
      const updated = await updateSavedCohort(id, { name: trimmed })
      setCohorts(prev => prev.map(c => c.id === id ? { ...c, name: updated.name } : c))
    } catch {
      alert('Failed to rename cohort.')
    }
  }

  async function handleDelete(id: number) {
    if (!window.confirm('Delete this saved cohort? This cannot be undone.')) return
    try {
      await deleteSavedCohort(id)
      setCohorts(prev => prev.filter(c => c.id !== id))
    } catch {
      alert('Failed to delete cohort. Please try again.')
    }
  }

  if (loading) return <p className="text-xs text-slate-500 italic py-2">Loading…</p>
  if (error) return <p className="text-xs text-red-400 py-2">{error}</p>
  if (cohorts.length === 0) return <p className="text-xs text-slate-500 italic py-2">No saved cohorts yet.</p>

  return (
    <div className="space-y-1.5">
      {cohorts.map(c => (
        <div key={c.id} className="bg-slate-700/50 rounded px-2 py-1.5 group">
          <div className="flex items-center justify-between gap-1">
            {editingId === c.id ? (
              <input
                ref={inputRef}
                value={editingName}
                onChange={e => setEditingName(e.target.value)}
                onBlur={() => commitRename(c.id)}
                onKeyDown={e => {
                  if (e.key === 'Enter') { e.preventDefault(); commitRename(c.id) }
                  if (e.key === 'Escape') setEditingId(null)
                }}
                className="flex-1 bg-slate-600 border border-teal-500 rounded px-1.5 py-0.5 text-xs text-white focus:outline-none"
              />
            ) : (
              <button
                onClick={() => onLoad(c.filters, c.id, c.name)}
                className="text-xs text-teal-400 hover:text-teal-300 font-medium text-left leading-tight truncate flex-1"
                title={c.description || c.name}
              >
                {c.name}
              </button>
            )}
            <div className="flex items-center gap-1 shrink-0">
              <button
                onClick={() => startEdit(c)}
                className="text-slate-600 hover:text-slate-300 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                title="Rename"
              >
                ✎
              </button>
              <button
                onClick={() => handleDelete(c.id)}
                className="text-slate-600 hover:text-red-400 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete"
              >
                ✕
              </button>
            </div>
          </div>
          {c.description && editingId !== c.id && (
            <p className="text-xs text-slate-500 mt-0.5 truncate">{c.description}</p>
          )}
        </div>
      ))}
    </div>
  )
}
