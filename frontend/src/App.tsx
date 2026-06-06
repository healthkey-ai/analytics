import { useState } from 'react'
import CohortPanel from './components/CohortPanel'
import Dashboard from './components/Dashboard'
import LoginPage from './components/Auth/LoginPage'
import { useAnalytics } from './hooks/useAnalytics'
import { useAuth } from './hooks/useAuth'
import type { CohortFilters } from './types'

export default function App() {
  const auth = useAuth()
  const { filters, settings, metrics, loading, updateFilter, clearFilters, setFilters } = useAnalytics()
  const [activeSavedCohortId, setActiveSavedCohortId] = useState<number | null>(null)

  if (auth.loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!auth.user) {
    return <LoginPage auth={auth} />
  }

  function handleLoadCohort(f: CohortFilters, cohortId?: number) {
    setFilters(f)
    setActiveSavedCohortId(cohortId ?? null)
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <CohortPanel
        filters={filters}
        settings={settings}
        onUpdate={updateFilter}
        onClear={clearFilters}
        cohortCount={metrics?.cohort.count ?? 0}
        onLoadCohort={handleLoadCohort}
      />
      <main className="flex-1 overflow-y-auto">
        <Dashboard
          metrics={metrics}
          loading={loading}
          disease={filters.disease ?? 'Multiple Myeloma'}
          user={auth.user}
          onLogout={auth.logout}
          activeSavedCohortId={activeSavedCohortId}
        />
      </main>
    </div>
  )
}
