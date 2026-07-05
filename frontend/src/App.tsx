import { useState } from 'react'
import CohortPanel from './components/CohortPanel'
import Dashboard from './components/Dashboard'
import LoginPage from './components/Auth/LoginPage'
import { useAnalytics } from './hooks/useAnalytics'
import { useAuth } from './hooks/useAuth'
import type { AuthState } from './hooks/useAuth'
import type { CohortFilters } from './types'

export default function App() {
  const auth = useAuth()

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

  return <AuthenticatedApp auth={auth} />
}

function AuthenticatedApp({ auth }: { auth: AuthState }) {
  const { filters, settings, metrics, loading, updateFilter, clearFilters, setFilters } = useAnalytics()
  const [activeSavedCohortId, setActiveSavedCohortId] = useState<number | null>(null)
  const [activeCohortName, setActiveCohortName] = useState<string | null>(null)
  const [cohortDirty, setCohortDirty] = useState(false)

  function handleLoadCohort(f: CohortFilters, cohortId?: number, cohortName?: string) {
    setFilters(f)
    setActiveSavedCohortId(cohortId ?? null)
    setActiveCohortName(cohortName ?? null)
    setCohortDirty(false)
  }

  function handleUpdateFilter<K extends keyof CohortFilters>(key: K, val: CohortFilters[K]) {
    if (activeSavedCohortId !== null) setCohortDirty(true)
    if (key === 'disease') {
      const disease = val as CohortFilters['disease']
      setFilters(prev => ({
        ...prev,
        disease,
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
      }))
      return
    }
    updateFilter(key, val)
  }

  function handleClearFilters() {
    setActiveSavedCohortId(null)
    setActiveCohortName(null)
    setCohortDirty(false)
    clearFilters()
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <CohortPanel
        filters={filters}
        settings={settings}
        onUpdate={handleUpdateFilter}
        onClear={handleClearFilters}
        cohortCount={metrics?.cohort.count ?? 0}
        onLoadCohort={handleLoadCohort}
        activeCohortName={activeCohortName}
        activeCohortId={activeSavedCohortId}
        cohortDirty={cohortDirty}
      />
      <main className="flex-1 overflow-y-auto">
        <Dashboard
          metrics={metrics}
          loading={loading}
          disease={filters.disease ?? 'Multiple Myeloma'}
          user={auth.user!}
          onLogout={auth.logout}
          activeSavedCohortId={activeSavedCohortId}
        />
      </main>
    </div>
  )
}
