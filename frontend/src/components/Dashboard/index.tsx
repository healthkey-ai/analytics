import { useState } from 'react'
import type { MetricsResponse } from '../../types'
import MetricCard from '../ui/MetricCard'
import ResponseRates from '../charts/ResponseRates'
import TreatmentPatterns from '../charts/TreatmentPatterns'
import TreatmentLines from '../charts/TreatmentLines'
import Demographics from '../charts/Demographics'
import StagingPanel from '../charts/StagingPanel'
import LabsPanel from '../charts/LabsPanel'
import TreatmentDuration from '../charts/TreatmentDuration'
import Sequences from '../charts/Sequences'

interface Props {
  metrics: MetricsResponse | null
  loading: boolean
  disease: string
}

type ResponseLineTab = '1L' | '2L' | '3L+'

function Spinner() {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/70 backdrop-blur-sm">
      <div className="flex flex-col items-center gap-3">
        <svg
          className="h-10 w-10 animate-spin text-teal-600"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 100 16v-4l-3 3 3 3v-4a8 8 0 01-8-8z"
          />
        </svg>
        <span className="text-sm text-gray-500 font-medium">Loading analytics…</span>
      </div>
    </div>
  )
}

export default function Dashboard({ metrics, loading }: Props) {
  const [responseTab, setResponseTab] = useState<ResponseLineTab>('1L')

  const cohortCount = metrics?.cohort?.count ?? 0
  const isEmpty = !loading && metrics !== null && cohortCount === 0

  const responseData =
    responseTab === '1L'
      ? metrics?.response_rates?.first_line ?? []
      : responseTab === '2L'
      ? metrics?.response_rates?.second_line ?? []
      : metrics?.response_rates?.later_line ?? []

  return (
    <div className="relative min-h-screen bg-gray-50">
      {loading && <Spinner />}

      {/* Top bar */}
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-gray-900">
            Multiple Myeloma Analytics
          </h1>
          {metrics && (
            <span className="inline-flex items-center rounded-full bg-teal-50 px-3 py-0.5 text-sm font-semibold text-teal-700 border border-teal-200">
              {cohortCount.toLocaleString()} patients
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400">Real-world evidence platform</p>
      </header>

      {/* Main content */}
      <main className="p-6 space-y-6 max-w-[1400px] mx-auto">
        {isEmpty ? (
          <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
            <svg
              className="h-12 w-12 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 17v-2m3 2v-4m3 4v-6M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p className="text-gray-500 font-medium">No patients match the current filters</p>
            <p className="text-sm text-gray-400">Try adjusting your cohort criteria</p>
          </div>
        ) : (
          <>
            {/* Row 1: Response Rates — full width with line tabs */}
            <MetricCard title="Response Rates" className="col-span-2">
              <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-4">
                {(['1L', '2L', '3L+'] as ResponseLineTab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setResponseTab(tab)}
                    className={`px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
                      responseTab === tab
                        ? 'bg-white text-gray-900 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab === '1L'
                      ? '1st Line'
                      : tab === '2L'
                      ? '2nd Line'
                      : '3rd Line+'}
                  </button>
                ))}
              </div>
              <ResponseRates
                data={responseData}
                title={
                  responseTab === '1L'
                    ? 'First-line therapy response rates'
                    : responseTab === '2L'
                    ? 'Second-line therapy response rates'
                    : 'Third-line+ therapy response rates'
                }
              />
            </MetricCard>

            {/* Row 2: Treatment Patterns + Treatment Lines */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="1st Line Treatment Patterns">
                <TreatmentPatterns
                  data={metrics?.treatment_patterns?.first_line ?? []}
                  title=""
                />
              </MetricCard>
              <MetricCard title="Lines of Therapy">
                <TreatmentLines
                  funnel={metrics?.treatment_patterns?.line_funnel ?? []}
                  distribution={metrics?.treatment_patterns?.line_distribution ?? []}
                />
              </MetricCard>
            </div>

            {/* Row 3: Demographics — full width */}
            <MetricCard title="Patient Demographics">
              {metrics?.demographics ? (
                <Demographics data={metrics.demographics} />
              ) : (
                <NoDataPlaceholder />
              )}
            </MetricCard>

            {/* Row 4: Staging — full width */}
            <MetricCard title="Disease Staging &amp; Characteristics">
              {metrics?.staging ? (
                <StagingPanel data={metrics.staging} />
              ) : (
                <NoDataPlaceholder />
              )}
            </MetricCard>

            {/* Row 5: Labs — full width */}
            <MetricCard title="Laboratory Values at Baseline">
              {metrics?.labs ? (
                <LabsPanel data={metrics.labs} />
              ) : (
                <NoDataPlaceholder />
              )}
            </MetricCard>

            {/* Row 6: Treatment Duration + Sequences */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard title="Treatment Duration">
                {metrics?.treatment_duration ? (
                  <TreatmentDuration data={metrics.treatment_duration} />
                ) : (
                  <NoDataPlaceholder />
                )}
              </MetricCard>
              <MetricCard title="Top Treatment Sequences">
                <Sequences
                  sequences={metrics?.treatment_patterns?.sequences ?? []}
                />
              </MetricCard>
            </div>
          </>
        )}
      </main>
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
