import { useState } from 'react'
import type { MetricsResponse } from '../../types'
import KMGroupChart from './KMGroupChart'
import LandmarkTable from './LandmarkTable'

interface Props {
  data: NonNullable<MetricsResponse['subgroup_survival']>
}

type StratKey   = 'by_stage' | 'by_cytogenetics' | 'by_sct' | 'by_mrd'
type OutcomeKey = 'os' | 'pfs'

const STRAT_CONFIG: { key: StratKey; label: string }[] = [
  { key: 'by_stage',        label: 'ISS Stage' },
  { key: 'by_cytogenetics', label: 'Cytogenetic Risk' },
  { key: 'by_sct',          label: 'SCT Status' },
  { key: 'by_mrd',          label: 'MRD Status' },
]

const OUTCOME_CONFIG: { key: OutcomeKey; label: string }[] = [
  { key: 'os',  label: 'OS' },
  { key: 'pfs', label: 'PFS' },
]

function PValueBadge({ p }: { p: number | null | undefined }) {
  if (p == null) return null
  const label = p < 0.001 ? 'p < 0.001' : p < 0.05 ? `p = ${p.toFixed(3)}` : `p = ${p.toFixed(2)}`
  return (
    <span className="inline-flex items-center rounded-full bg-gray-100 border border-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600">
      {label}
    </span>
  )
}

export default function SubgroupSurvival({ data }: Props) {
  const [strat,   setStrat]   = useState<StratKey>('by_stage')
  const [outcome, setOutcome] = useState<OutcomeKey>('os')

  const lines = data[strat][outcome]
  const pValue = outcome === 'os' ? data[strat].os_p : data[strat].pfs_p

  const toggleClass = (active: boolean) =>
    `px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
      active ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
    }`

  if (!lines || lines.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available for this stratification
      </div>
    )
  }

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-wrap gap-3 mb-4">
        <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit">
          {STRAT_CONFIG.map(({ key, label }) => (
            <button key={key} onClick={() => setStrat(key)} className={toggleClass(strat === key)}>
              {label}
            </button>
          ))}
        </div>
        <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit">
          {OUTCOME_CONFIG.map(({ key, label }) => (
            <button key={key} onClick={() => setOutcome(key)} className={toggleClass(outcome === key)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      <KMGroupChart lines={lines} legendExtra={<PValueBadge p={pValue} />} />

      <p className="text-xs text-gray-400 mt-2">
        <span className="font-medium">OS</span>: 1L start → death. &nbsp;
        <span className="font-medium">PFS</span>: 1L start → first progression (any line) or death. &nbsp;
        Patients without an event are censored at last known contact. Dashed line = 50%. Shaded bands = 95% CI.
      </p>

      <LandmarkTable lines={lines} />
    </div>
  )
}
