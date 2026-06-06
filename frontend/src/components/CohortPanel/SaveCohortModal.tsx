import { useState } from 'react'
import { createSavedCohort, updateSavedCohort } from '../../api/client'
import type { CohortFilters, SavedCohort } from '../../types'

interface Props {
  filters: CohortFilters
  activeCohortId?: number
  activeCohortName?: string
  onSaved: (cohort: SavedCohort) => void
  onClose: () => void
}

export default function SaveCohortModal({ filters, activeCohortId, activeCohortName, onSaved, onClose }: Props) {
  const [name, setName] = useState(activeCohortName ?? '')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleUpdate() {
    if (!activeCohortId) return
    setSaving(true)
    setError('')
    try {
      const cohort = await updateSavedCohort(activeCohortId, { filters })
      onSaved(cohort)
    } catch {
      setError('Failed to update cohort.')
      setSaving(false)
    }
  }

  async function handleSaveNew(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setError('Name is required.'); return }
    setSaving(true)
    setError('')
    try {
      const cohort = await createSavedCohort({ name: name.trim(), description, filters })
      onSaved(cohort)
    } catch {
      setError('Failed to save cohort.')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={onClose}>
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 w-80 shadow-2xl" onClick={e => e.stopPropagation()}>
        <h3 className="text-sm font-bold text-white mb-4">Save Cohort</h3>

        {activeCohortId && (
          <>
            <button
              onClick={handleUpdate}
              disabled={saving}
              className="w-full text-sm bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold rounded px-3 py-2 transition-colors"
            >
              {saving ? 'Saving…' : `Update "${activeCohortName}"`}
            </button>
            <div className="flex items-center gap-2 my-4">
              <div className="flex-1 h-px bg-slate-700" />
              <span className="text-xs text-slate-500">or save as new</span>
              <div className="flex-1 h-px bg-slate-700" />
            </div>
          </>
        )}

        <form onSubmit={handleSaveNew} className="space-y-3">
          <div>
            <label className="block text-xs text-slate-400 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              autoFocus={!activeCohortId}
              placeholder="e.g. High-risk MM triple refractory"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
            />
          </div>
          <div>
            <label className="block text-xs text-slate-400 mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              placeholder="Optional notes"
              className="w-full bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500 resize-none"
            />
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 text-sm text-slate-400 hover:text-white border border-slate-600 rounded px-3 py-1.5 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 text-sm bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold rounded px-3 py-1.5 transition-colors"
            >
              {saving ? 'Saving…' : 'Save as new'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
