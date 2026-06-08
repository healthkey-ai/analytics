import { useState, useEffect, useRef } from 'react'
import type { MetricsResponse, User } from '../../types'
import MetricCard from '../ui/MetricCard'
import ResponseRates from '../charts/ResponseRates'
import TreatmentPatterns from '../charts/TreatmentPatterns'
import TreatmentLines from '../charts/TreatmentLines'
import Demographics from '../charts/Demographics'
import StagingPanel from '../charts/StagingPanel'
import LabsPanel from '../charts/LabsPanel'
import TreatmentDuration from '../charts/TreatmentDuration'
import Sequences from '../charts/Sequences'
import SurvivalCurves from '../charts/SurvivalCurves'
import TTNT from '../charts/TTNT'
import Switching from '../charts/Switching'
import SubgroupSurvival from '../charts/SubgroupSurvival'
import DurationOfResponse from '../charts/DurationOfResponse'
import api from '../../api/client'

interface Props {
  metrics: MetricsResponse | null
  loading: boolean
  disease: string
  user: User
  onLogout: () => void
  activeSavedCohortId: number | null
}

type DashboardTab    = 'outcomes' | 'profile'
type ResponseLineTab = '1L' | '2L' | '3L+'

function Spinner() {
  return (
    <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/70 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3">
        <svg className="h-10 w-10 animate-spin text-teal-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z" />
        </svg>
        <span className="text-sm text-gray-500 font-medium">Loading analytics…</span>
      </div>
    </div>
  )
}

function NoDataPlaceholder() {
  return (
    <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
      No data available
    </div>
  )
}

export default function Dashboard({ metrics, loading, disease, user, onLogout, activeSavedCohortId }: Props) {
  const [tab, setTab]                 = useState<DashboardTab>('outcomes')
  const [responseTab, setResponseTab] = useState<ResponseLineTab>('1L')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const exportMenuRef = useRef<HTMLDivElement>(null)

  // Close export dropdown on outside click
  useEffect(() => {
    if (!showExportMenu) return
    function close(e: MouseEvent) {
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setShowExportMenu(false)
      }
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [showExportMenu])

  const cohortCount = metrics?.cohort?.count ?? 0
  const isEmpty     = !loading && metrics !== null && cohortCount === 0

  const responseData =
    responseTab === '1L' ? metrics?.response_rates?.first_line ?? []
    : responseTab === '2L' ? metrics?.response_rates?.second_line ?? []
    : metrics?.response_rates?.later_line ?? []

  const TABS: { id: DashboardTab; label: string }[] = [
    { id: 'outcomes', label: 'Outcomes' },
    { id: 'profile',  label: 'Patient Profile' },
  ]

  async function handleExport(format: 'csv' | 'json') {
    setShowExportMenu(false)
    if (!activeSavedCohortId) {
      alert('Save your current cohort first (use the "Save" button in the left panel), then export.')
      return
    }
    try {
      const resp = await api.get(
        `/cohorts/saved/${activeSavedCohortId}/export/?file_format=${format}`,
        { responseType: 'blob' }
      )
      const url = URL.createObjectURL(new Blob([resp.data]))
      const a = document.createElement('a')
      const disposition = resp.headers['content-disposition'] ?? ''
      const match = disposition.match(/filename="([^"]+)"/)
      a.href = url
      a.download = match ? match[1] : `cohort.${format}`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      alert('Export failed. Please try again.')
    }
  }

  return (
    <div className="relative min-h-screen bg-gray-50">
      {loading && <Spinner />}

      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-gray-900">{disease} Analytics</h1>
          {metrics && (
            <span className="inline-flex items-center rounded-full bg-teal-50 px-3 py-0.5 text-sm font-semibold text-teal-700 border border-teal-200">
              {cohortCount.toLocaleString()} patients
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* User + logout */}
          <span className="text-sm text-gray-500">{user.name || user.email}</span>
          <button
            onClick={onLogout}
            className="text-sm text-gray-400 hover:text-red-500 transition-colors"
            title="Sign out"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Tab bar */}
      <div className="sticky top-[73px] z-10 bg-white border-b border-gray-200 px-6">
        <div className="flex items-center justify-between max-w-[1400px] mx-auto">
          <div className="flex">
            {TABS.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setTab(id)}
                className={`px-5 py-3 text-sm font-semibold border-b-2 transition-colors ${
                  tab === id
                    ? 'border-teal-600 text-teal-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Export dropdown */}
          <div className="relative" ref={exportMenuRef}>
            <button
              onClick={() => setShowExportMenu(v => !v)}
              className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export
            </button>
            {showExportMenu && (
              <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1 min-w-[120px]">
                <button onClick={() => handleExport('csv')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">CSV</button>
                <button onClick={() => handleExport('json')} className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50">JSON</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="p-6 space-y-6 max-w-[1400px] mx-auto">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
            <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 17v-2m3 2v-4m3 4v-6M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-gray-500 font-medium">No patients match the current filters</p>
            <p className="text-sm text-gray-400">Try adjusting your cohort criteria</p>
          </div>
        ) : tab === 'outcomes' ? (
          <>
            <MetricCard title="Progression-Free Survival">
              {metrics?.survival ? <SurvivalCurves data={metrics.survival} /> : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard title="Survival by Subgroup">
              {metrics?.subgroup_survival
                ? <SubgroupSurvival data={metrics.subgroup_survival} />
                : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard title="Response Rates">
              <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-4">
                {(['1L', '2L', '3L+'] as ResponseLineTab[]).map((t) => (
                  <button
                    key={t}
                    onClick={() => setResponseTab(t)}
                    className={`px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
                      responseTab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {t === '1L' ? '1st Line' : t === '2L' ? '2nd Line' : '3rd Line+'}
                  </button>
                ))}
              </div>
              <ResponseRates
                data={responseData}
                title={
                  responseTab === '1L' ? 'First-line therapy response rates'
                  : responseTab === '2L' ? 'Second-line therapy response rates'
                  : 'Third-line+ therapy response rates'
                }
              />
            </MetricCard>

            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="1st Line Treatment Patterns">
                <TreatmentPatterns data={metrics?.treatment_patterns?.first_line ?? []} title="" />
              </MetricCard>
              <MetricCard title="Lines of Therapy">
                <TreatmentLines
                  funnel={metrics?.treatment_patterns?.line_funnel ?? []}
                  distribution={metrics?.treatment_patterns?.line_distribution ?? []}
                />
              </MetricCard>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="Treatment Duration">
                {metrics?.treatment_duration ? <TreatmentDuration data={metrics.treatment_duration} /> : <NoDataPlaceholder />}
              </MetricCard>
              <MetricCard title="Top Treatment Sequences">
                <Sequences sequences={metrics?.treatment_patterns?.sequences ?? []} />
              </MetricCard>
            </div>

            {/* TTNT + Switching */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="Time to Next Treatment (TTNT)">
                {metrics?.ttnt ? <TTNT data={metrics.ttnt} /> : <NoDataPlaceholder />}
              </MetricCard>
              <MetricCard title="Treatment Switching Patterns">
                {metrics?.switching ? <Switching data={metrics.switching} /> : <NoDataPlaceholder />}
              </MetricCard>
            </div>

            <MetricCard title="Duration of Response (DOR)">
              {metrics?.dor ? <DurationOfResponse data={metrics.dor} /> : <NoDataPlaceholder />}
            </MetricCard>
          </>
        ) : (
          <>
            <MetricCard title="Patient Demographics">
              {metrics?.demographics ? <Demographics data={metrics.demographics} /> : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard title="Disease Staging &amp; Characteristics">
              {metrics?.staging ? <StagingPanel data={metrics.staging} /> : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard title="Laboratory Values at Baseline">
              {metrics?.labs ? <LabsPanel data={metrics.labs} /> : <NoDataPlaceholder />}
            </MetricCard>
          </>
        )}
      </main>
    </div>
  )
}
