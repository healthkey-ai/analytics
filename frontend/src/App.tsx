import CohortPanel from './components/CohortPanel'
import Dashboard from './components/Dashboard'
import { useAnalytics } from './hooks/useAnalytics'

export default function App() {
  const { filters, settings, metrics, loading, updateFilter, clearFilters } = useAnalytics()

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <CohortPanel
        filters={filters}
        settings={settings}
        onUpdate={updateFilter}
        onClear={clearFilters}
        cohortCount={metrics?.cohort.count ?? 0}
      />
      <main className="flex-1 overflow-y-auto">
        <Dashboard
          metrics={metrics}
          loading={loading}
          disease={filters.disease ?? 'Multiple Myeloma'}
        />
      </main>
    </div>
  )
}
