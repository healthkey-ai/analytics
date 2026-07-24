import { useState, useRef } from 'react'
import type { CohortFilters, MetricsResponse, User } from '../../types'
import { useOutsideClick } from '../../hooks/useOutsideClick'
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
import PathwaySunburst from '../charts/PathwaySunburst'
import DurationOfResponse from '../charts/DurationOfResponse'
import TreatmentSankey from '../charts/TreatmentSankey'
import ForestPlot from '../charts/ForestPlot'
import CohortCharacterization from '../charts/CohortCharacterization'
import IncidenceChart from '../charts/IncidenceChart'
import TimeToTreatment from '../charts/TimeToTreatment'
import DiseaseStateSnapshot from '../charts/DiseaseStateSnapshot'
import EligibilityFunnel from '../charts/EligibilityFunnel'
import TherapyCategories from '../charts/TherapyCategories'
import PathwayOutcomes from '../charts/PathwayOutcomes'
import Pod24 from '../charts/Pod24'
import LandmarkResponse from '../charts/LandmarkResponse'
import TransformationChart from '../charts/TransformationChart'
import api from '../../api/client'

interface Props {
  metrics: MetricsResponse | null
  loading: boolean
  disease: string
  user: User
  onLogout: () => void
  activeSavedCohortId: number | null
  filters: CohortFilters
}

type DashboardTab    = 'outcomes' | 'treatments' | 'profile'
type ResponseLineTab = '1L' | '2L' | '3L+'
type PatternLineTab  = '1L' | '2L' | '3L+' | 'overall'

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

function EligibilityCard({ data, onExport }: { data: NonNullable<MetricsResponse['eligibility']>; onExport?: (format: 'csv' | 'json') => void }) {
  return (
    <MetricCard
      title="Eligibility / Feasibility Counts"
      description="How many patients fit the current profile — the cumulative count remaining after each filter group, from the full visible population down to the eligible set. De-identified aggregate counts only, for feasibility and trial-sizing questions."
      onExport={onExport}
    >
      <EligibilityFunnel data={data} />
    </MetricCard>
  )
}

export default function Dashboard({ metrics, loading, disease, user, onLogout, activeSavedCohortId, filters }: Props) {
  const canExport = user.is_premium === true || user.is_staff === true || user.role === 'admin'
  const isMultipleMyeloma = disease === 'Multiple Myeloma'
  const isFollicularLymphoma = disease === 'Follicular Lymphoma'
  const [tab, setTab]                 = useState<DashboardTab>('outcomes')
  const [responseTab, setResponseTab] = useState<ResponseLineTab>('1L')
  const [patternTab, setPatternTab]   = useState<PatternLineTab>('1L')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const exportMenuRef = useRef<HTMLDivElement>(null)
  useOutsideClick(exportMenuRef, () => setShowExportMenu(false), showExportMenu)

  const cohortCount = metrics?.cohort?.count ?? 0
  const isEmpty     = !loading && metrics !== null && cohortCount === 0

  const responseData =
    responseTab === '1L' ? metrics?.response_rates?.first_line ?? []
    : responseTab === '2L' ? metrics?.response_rates?.second_line ?? []
    : metrics?.response_rates?.later_line ?? []

  const patternData =
    patternTab === '1L' ? metrics?.treatment_patterns?.first_line ?? []
    : patternTab === '2L' ? metrics?.treatment_patterns?.second_line ?? []
    : patternTab === '3L+' ? metrics?.treatment_patterns?.later_line ?? []
    : metrics?.treatment_patterns?.overall ?? []

  const TABS: { id: DashboardTab; label: string }[] = [
    { id: 'outcomes',   label: 'Outcomes' },
    { id: 'treatments', label: 'Treatments' },
    { id: 'profile',    label: 'Patient Profile' },
  ]

  function toFilterParams(): URLSearchParams {
    const p = new URLSearchParams()
    for (const [key, val] of Object.entries(filters)) {
      if (val === undefined || val === null || val === '') continue
      if (Array.isArray(val)) {
        val.forEach((v: string | number) => p.append(key, String(v)))
      } else {
        p.set(key, String(val))
      }
    }
    return p
  }

  function chartExportHandler(chartKey: string): (format: 'csv' | 'json') => void {
    return async (format: 'csv' | 'json') => {
      const p = toFilterParams()
      p.set('chart', chartKey)
      p.set('file_format', format)
      try {
        if (format === 'csv') {
          const resp = await api.get(`/metrics/export/?${p.toString()}`, { responseType: 'blob' })
          const url = URL.createObjectURL(new Blob([resp.data]))
          const a = document.createElement('a')
          a.href = url
          a.download = `${chartKey}_export.csv`
          a.click()
          URL.revokeObjectURL(url)
        } else {
          const resp = await api.get(`/metrics/export/?${p.toString()}`, { responseType: 'blob' })
          const url = URL.createObjectURL(new Blob([resp.data], { type: 'application/json' }))
          const a = document.createElement('a')
          a.href = url
          a.download = `${chartKey}_export.json`
          a.click()
          URL.revokeObjectURL(url)
        }
      } catch {
        alert('Export failed. Please try again.')
      }
    }
  }

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
      <header className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        {/* Title row */}
        <div className="px-6 py-4 flex items-center justify-between">
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
            {canExport ? (
              <>
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
              </>
            ) : (
              <button
                disabled
                title="Premium or staff access required"
                className="flex items-center gap-1.5 text-sm text-gray-400 border border-gray-200 rounded-lg px-3 py-1.5 cursor-not-allowed opacity-60"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Export
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <main className="p-6 space-y-6 max-w-[1400px] mx-auto">
        {isEmpty ? (
          <>
            {metrics?.eligibility && metrics.eligibility.total > 0 && (
              <EligibilityCard data={metrics.eligibility} onExport={canExport ? chartExportHandler('eligibility') : undefined} />
            )}
            <div className="flex flex-col items-center justify-center h-64 gap-3 text-center">
              <svg className="h-12 w-12 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 17v-2m3 2v-4m3 4v-6M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-gray-500 font-medium">No patients match the current filters</p>
              <p className="text-sm text-gray-400">Try adjusting your cohort criteria</p>
            </div>
          </>
        ) : tab === 'outcomes' ? (
          <>
            <MetricCard
              title="Progression-Free Survival"
              description="Kaplan-Meier curve showing the probability of patients remaining progression-free or alive over time from first-line therapy start. The median PFS is the time point at which 50% of patients have experienced progression or death. Shaded area represents the 95% confidence interval."
            
              onExport={canExport ? chartExportHandler('survival') : undefined}>
              {metrics?.survival ? <SurvivalCurves data={metrics.survival} /> : <NoDataPlaceholder />}
            </MetricCard>

            {isMultipleMyeloma && (
              <MetricCard
                title="Survival by Subgroup"
                description="Kaplan-Meier survival curves stratified by ISS disease stage, cytogenetic risk (high-risk vs. standard-risk), and SCT history. Patients without a cytogenetics workup are excluded from the risk subgroups. Enables side-by-side comparison of outcomes across biologically distinct patient populations."
              
              onExport={canExport ? chartExportHandler('subgroup_survival') : undefined}>
                {metrics?.subgroup_survival
                  ? <SubgroupSurvival data={metrics.subgroup_survival} />
                  : <NoDataPlaceholder />}
              </MetricCard>
            )}

            {metrics?.landmark_survival && metrics.landmark_survival.n > 0 && (
              <MetricCard
                title={`Landmark Overall Survival (${metrics.landmark_survival.landmark_months}-month landmark, n = ${metrics.landmark_survival.n})`}
                description="Overall survival measured from a fixed landmark time point, including only patients who were alive and event-free at that point. This method eliminates early-death bias and estimates survival conditional on reaching the landmark — a standard technique when comparing outcomes across different treatment eras."
              
              onExport={canExport ? chartExportHandler('landmark_survival') : undefined}>
                <SurvivalCurves data={{
                  os:  metrics.landmark_survival,
                  pfs: { curve: [], n: 0, median: null },
                  efs: { curve: [], n: 0, median: null },
                }} />
              </MetricCard>
            )}

            <MetricCard
              title="Response Rates"
              description="Best response to therapy across each treatment line (1st, 2nd, 3rd+). Responses are classified by depth: sCR (stringent complete response), CR (complete response), VGPR (very good partial response), PR (partial response), SD (stable disease), and PD (progressive disease), per standard disease-specific criteria."
            
              onExport={canExport ? chartExportHandler('response_rates') : undefined}>
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

            {isFollicularLymphoma && metrics?.pod24 && (
              <MetricCard
                title="POD24 Split"
                description="Separates patients who progressed within 24 months of starting first-line therapy (POD24) — a group with markedly worse outcomes in follicular lymphoma — from those who did not, and compares overall survival from the 24-month landmark between the two groups. The clock starts at first-line treatment start, stated explicitly because landmark definitions vary. Patients censored before 24 months without an event are unevaluable."
              
              onExport={canExport ? chartExportHandler('pod24') : undefined}>
                <Pod24 data={metrics.pod24} />
              </MetricCard>
            )}

            {isFollicularLymphoma && metrics?.landmark_response && (
              <MetricCard
                title="Complete Response by Landmark (CR30)"
                description="Proportion of evaluable first-line patients who achieved a complete response within 12, 24, 30, or 36 months of starting first-line therapy. CR30 (complete response at 30 months) is a follicular-lymphoma-specific depth-of-response measure. The clock starts at first-line treatment start."
              
              onExport={canExport ? chartExportHandler('landmark_response') : undefined}>
                <LandmarkResponse data={metrics.landmark_response} />
              </MetricCard>
            )}

            {metrics?.pathway_outcomes && metrics.pathway_outcomes.pathways.length > 0 && (
              <MetricCard
                title="Outcomes by Treatment Pathway"
                description="Overall survival compared across the most common first-line → second-line pathway combinations in the cohort (e.g. BR → R-CHOP vs R-CHOP → R²). Only pathways with enough patients are shown — small pathways produce unreliable curves."
              
              onExport={canExport ? chartExportHandler('pathway_outcomes') : undefined}>
                <PathwayOutcomes data={metrics.pathway_outcomes} />
              </MetricCard>
            )}

            {isFollicularLymphoma && metrics?.transformation && (
              <MetricCard
                title="Transformation to Aggressive Lymphoma (DLBCL)"
                description="Histologic transformation of follicular lymphoma to DLBCL — a clinically pivotal event. Shows how many patients transformed, when (months from diagnosis), and how they did afterward: outcome distribution and overall survival measured from the transformation date. Shown only where a transformation is documented; not every patient is biopsied at progression, so the true rate may be higher."
              
              onExport={canExport ? chartExportHandler('transformation') : undefined}>
                <TransformationChart data={metrics.transformation} />
              </MetricCard>
            )}

            <MetricCard
              title="Duration of Response (DOR)"
              description="Time from first documented response (≥PR) to disease progression or death among patients who responded to therapy. Presented as a Kaplan-Meier curve for responders only. DOR measures the durability of treatment benefit and complements overall response rate — a high ORR with short DOR indicates transient rather than sustained disease control."
            
              onExport={canExport ? chartExportHandler('dor') : undefined}>
              {metrics?.dor ? <DurationOfResponse data={metrics.dor} /> : <NoDataPlaceholder />}
            </MetricCard>

            {isMultipleMyeloma && (
              <MetricCard
                title="Subgroup Forest Plot — Overall Survival"
                description="Hazard ratios (HR) for overall survival across prespecified subgroups. Each row shows the HR and 95% confidence interval for a subgroup relative to its complement. An HR < 1 (left of center) indicates better survival in that subgroup. Wide confidence intervals reflect small sample sizes within the subgroup."
              
              onExport={canExport ? chartExportHandler('forest_plot') : undefined}>
                <ForestPlot data={metrics?.forest_plot ?? []} />
              </MetricCard>
            )}
          </>
        ) : tab === 'treatments' ? (
          <>
            {/* Treatment Pathways: sunburst + Sankey side by side */}
            <MetricCard
              title="Treatment Pathways (OHDSI-Style)"
              description="Visualizes real-world treatment sequences using the OHDSI Treatment Pathways methodology. The sunburst chart shows how patients flow through lines of therapy, with each ring representing a successive treatment line and segment size proportional to patient count. The Sankey diagram shows the same flows as directed transitions, making it easy to identify the most common sequencing patterns."
            
              onExport={canExport ? chartExportHandler('pathway_sunburst') : undefined}>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Pathway Sunburst</h3>
                  {metrics?.pathway_sunburst
                    ? <PathwaySunburst data={metrics.pathway_sunburst} />
                    : <NoDataPlaceholder />}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Treatment Flow (Sankey)</h3>
                  {metrics?.switching
                    ? <TreatmentSankey data={metrics.switching} />
                    : <NoDataPlaceholder />}
                </div>
              </div>
            </MetricCard>

            {/* Treatment Patterns by Line + Lines of Therapy */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard
                title="Treatment Patterns by Line"
                description="Distribution of regimens used in the cohort, ranked by frequency, broken down by line of therapy. The Overall tab shows how many patients received each regimen in any line (a patient counts once per regimen). Helps identify dominant treatment approaches and variation in prescribing practice across lines."
              
              onExport={canExport ? chartExportHandler('treatment_patterns') : undefined}>
                <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-4">
                  {(['1L', '2L', '3L+', 'overall'] as PatternLineTab[]).map((t) => (
                    <button
                      key={t}
                      onClick={() => setPatternTab(t)}
                      className={`px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
                        patternTab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                      }`}
                    >
                      {t === '1L' ? '1st Line' : t === '2L' ? '2nd Line' : t === '3L+' ? '3rd Line+' : 'Overall'}
                    </button>
                  ))}
                </div>
                <TreatmentPatterns data={patternData} title="" />
              </MetricCard>
              <MetricCard
                title="Lines of Therapy & Treatment Burden"
                description="How heavily pre-treated the cohort is: median lines of therapy received and the share of patients reaching two or more (and three or more) lines. Left: a funnel showing how many patients advanced to each successive line of therapy, illustrating attrition as treatment progresses. Right: distribution of the total number of treatment lines each patient received."
              
              onExport={canExport ? chartExportHandler('treatment_patterns') : undefined}>
                <TreatmentLines
                  funnel={metrics?.treatment_patterns?.line_funnel ?? []}
                  distribution={metrics?.treatment_patterns?.line_distribution ?? []}
                  burden={metrics?.treatment_patterns?.burden}
                />
              </MetricCard>
            </div>

            {/* Therapy Categories */}
            <MetricCard
              title="Therapy Categories by Line"
              description="Regimens grouped into therapy categories — bispecific antibodies, CAR-T, chemotherapy-containing, immunomodulatory (IMiD), monoclonal antibodies, targeted/small-molecule, and endocrine therapies — shown per line of therapy. Combination regimens can belong to more than one category (e.g. R-CHOP is both chemotherapy-containing and a monoclonal-antibody regimen), so percentages need not sum to 100."
            
              onExport={canExport ? chartExportHandler('treatment_patterns') : undefined}>
              {metrics?.therapy_categories
                ? <TherapyCategories data={metrics.therapy_categories} />
                : <NoDataPlaceholder />}
            </MetricCard>

            {/* Treatment Duration + Sequences */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard
                title="Treatment Duration"
                description="Median time on therapy for each treatment line, calculated from line start date to end date (or last follow-up if ongoing). Longer duration indicates better tolerability or sustained disease control. Box plots show the interquartile range; whiskers extend to the 5th and 95th percentiles."
              
              onExport={canExport ? chartExportHandler('treatment_duration') : undefined}>
                {metrics?.treatment_duration ? <TreatmentDuration data={metrics.treatment_duration} /> : <NoDataPlaceholder />}
              </MetricCard>
              <MetricCard
                title="Top Treatment Sequences"
                description="The most common multi-line treatment sequences observed in the cohort (e.g., VRd → Kd → DPd). Each sequence lists the regimens in order of administration; the count shows how many patients followed that exact path. Reveals dominant sequencing patterns and how often patients return to earlier drug classes."
              
              onExport={canExport ? chartExportHandler('treatment_patterns') : undefined}>
                <Sequences sequences={metrics?.treatment_patterns?.sequences ?? []} />
              </MetricCard>
            </div>

            <MetricCard
              title="Time to First Treatment"
              description="Distribution of time (in days) from diagnosis date to start of first-line therapy. Short intervals suggest prompt initiation; long intervals may reflect watchful waiting, delayed diagnosis, or access barriers. The histogram shows the count of patients in each time bucket; the median and IQR are annotated."
            
              onExport={canExport ? chartExportHandler('time_to_treatment') : undefined}>
              {metrics?.time_to_treatment
                ? <TimeToTreatment data={metrics.time_to_treatment} />
                : <NoDataPlaceholder />}
            </MetricCard>

            {/* TTNT + Switching */}
            <div className="grid grid-cols-2 gap-6">
              <MetricCard
                title="Time to Next Treatment (TTNT)"
                description="Kaplan-Meier estimate of time from end of one therapy to initiation of the next. TTNT is a real-world surrogate for time to progression that avoids dependence on formal response assessments — treatment change serves as the event. Shorter TTNT indicates faster progression or toxicity-driven discontinuation."
              
              onExport={canExport ? chartExportHandler('ttnt') : undefined}>
                {metrics?.ttnt ? <TTNT data={metrics.ttnt} /> : <NoDataPlaceholder />}
              </MetricCard>
              <MetricCard
                title="Treatment Switching Patterns"
                description="Flow diagram showing transitions between regimens across treatment lines. The width of each flow is proportional to the number of patients making that switch. Highlights which drug classes patients move to after each line and identifies the most common escape pathways following treatment failure."
              
              onExport={canExport ? chartExportHandler('switching') : undefined}>
                {metrics?.switching ? <Switching data={metrics.switching} /> : <NoDataPlaceholder />}
              </MetricCard>
            </div>

          </>
        ) : (
          <>
            {metrics?.disease_state && metrics.disease_state.total > 0 && (
              <MetricCard
                title="Disease-State Snapshot"
                description="At-a-glance breakdown of where patients are in their disease journey: newly diagnosed, on watch-and-wait, in remission, or relapsed/refractory. States are derived from treatment history and outcomes (no explicit field exists): relapsed/refractory = 2+ lines, a recorded relapse, any later-line therapy recorded, or progressive disease; in remission = responded to first-line with no later line; watch-and-wait = diagnosed over 6 months ago and never treated; newly diagnosed = diagnosed within the last 6 months and not yet treated."
              
              onExport={canExport ? chartExportHandler('disease_state') : undefined}>
                <DiseaseStateSnapshot data={metrics.disease_state} />
              </MetricCard>
            )}

            {metrics?.eligibility && metrics.eligibility.total > 0 && (
              <EligibilityCard data={metrics.eligibility} onExport={canExport ? chartExportHandler('eligibility') : undefined} />
            )}

            {metrics?.cohort_characterization && metrics.cohort_characterization.n > 0 && (
              <MetricCard
                title="Cohort Characterization (Table 1)"
                description="Summary of baseline patient characteristics in the standard clinical research 'Table 1' format. Continuous variables are reported as median (IQR); categorical variables as count (%). Provides a quick audit of cohort composition — demographics, disease stage, performance status, comorbidities, and key lab values — before interpreting outcomes data."
              
              onExport={canExport ? chartExportHandler('cohort_characterization') : undefined}>
                <CohortCharacterization data={metrics.cohort_characterization} />
              </MetricCard>
            )}

            <MetricCard
              title="New Diagnoses & Treatment Starts Over Time"
              description="Monthly or quarterly counts of new diagnoses and first-line treatment initiations plotted over the observation period. Useful for identifying enrollment trends, seasonal patterns, or changes in diagnostic practice. A growing gap between diagnosis and treatment-start lines may signal delayed care access over time."
            
              onExport={canExport ? chartExportHandler('incidence') : undefined}>
              {metrics?.incidence && metrics.incidence.length > 0
                ? <IncidenceChart data={metrics.incidence} />
                : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard
              title="Patient Demographics"
              description="Distribution of age, sex, race, and ethnicity across the cohort. Age is shown as a histogram; categorical variables as proportional bar charts. Demographic composition affects generalizability — a cohort skewed toward younger or healthier patients may not reflect real-world outcomes in a broader population."
            
              onExport={canExport ? chartExportHandler('demographics') : undefined}>
              {metrics?.demographics ? <Demographics data={metrics.demographics} /> : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard
              title="Disease Staging & Characteristics"
              description="Distribution of ISS/R-ISS staging, cytogenetic risk groups (high-risk vs. standard-risk), SCT eligibility and history, CRAB criteria, and other disease-defining characteristics at baseline. Higher proportions of ISS Stage III or high-risk cytogenetics indicate a more aggressive disease population."
            
              onExport={canExport ? chartExportHandler('staging') : undefined}>
              {metrics?.staging ? <StagingPanel data={metrics.staging} /> : <NoDataPlaceholder />}
            </MetricCard>

            <MetricCard
              title="Laboratory Values at Baseline"
              description="Key lab values recorded at or near diagnosis: M-protein (serum and urine), beta-2 microglobulin, creatinine, hemoglobin, LDH, calcium, and others. Values are shown as box plots (median, IQR, range). Reference ranges are overlaid where applicable; values outside normal limits are highlighted in red."
            
              onExport={canExport ? chartExportHandler('labs') : undefined}>
              {metrics?.labs ? <LabsPanel data={metrics.labs} /> : <NoDataPlaceholder />}
            </MetricCard>
          </>
        )}
      </main>
    </div>
  )
}
