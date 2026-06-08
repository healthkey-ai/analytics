import { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { MetricsResponse } from '../../types'
import { mergeKMCurves } from '../../utils/kmChartUtils'
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

const COLORS = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed']

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

  const chartData = useMemo(
    () => mergeKMCurves(lines.map((l, i) => ({ key: `g${i}`, curve: l.curve }))),
    [lines]
  )

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

      {/* Legend + p-value badge */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <div className="flex flex-wrap gap-6">
          {lines.map((line, i) => (
            <div key={line.label} className="flex items-center gap-2">
              <span className="inline-block w-8 h-0.5" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              <span className="text-xs text-gray-600">
                <span className="font-semibold">{line.label}</span>
                {' · n='}{line.n}
                {line.median != null
                  ? ` · median ${line.median.toFixed(1)} mo`
                  : ' · median NR'}
              </span>
            </div>
          ))}
        </div>
        <PValueBadge p={pValue} />
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 4, right: 24, left: 0, bottom: 24 }}>
          <XAxis
            dataKey="time"
            type="number"
            label={{ value: 'Months from 1st-line start', position: 'insideBottom', offset: -12, fontSize: 11 }}
            tick={{ fontSize: 11 }}
            domain={[0, 'auto']}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fontSize: 11 }}
            label={{ value: 'Survival probability', angle: -90, position: 'insideLeft', fontSize: 11, offset: 10 }}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown, name: unknown) => {
              const nameStr = String(name)
              if (nameStr.endsWith('_lower') || nameStr.endsWith('_upper')) return null
              const idx = Number(nameStr.replace('g', ''))
              const label = lines[idx]?.label ?? nameStr
              return [`${(Number(v) * 100).toFixed(1)}%`, label]
            }) as any}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={((t: number) => `${t} months`) as any}
            contentStyle={{ fontSize: 12 }}
          />
          <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" />
          {lines.map((line, i) => (
            <Line
              key={line.label}
              type="stepAfter"
              dataKey={`g${i}`}
              name={`g${i}`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
          {/* CI bands — dashed, low opacity, excluded from legend/tooltip */}
          {lines.map((line, i) => [
            <Line
              key={`${line.label}_lower`}
              type="stepAfter"
              dataKey={`g${i}_lower`}
              name={`g${i}_lower`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={1}
              strokeOpacity={0.3}
              strokeDasharray="3 3"
              dot={false}
              legendType="none"
            />,
            <Line
              key={`${line.label}_upper`}
              type="stepAfter"
              dataKey={`g${i}_upper`}
              name={`g${i}_upper`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={1}
              strokeOpacity={0.3}
              strokeDasharray="3 3"
              dot={false}
              legendType="none"
            />,
          ])}
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-400 mt-2">
        <span className="font-medium">OS</span>: 1L start → death. &nbsp;
        <span className="font-medium">PFS</span>: 1L start → first progression (any line) or death. &nbsp;
        Patients without an event are censored at last known contact. Dashed line = 50%. Shaded bands = 95% CI.
      </p>

      <LandmarkTable lines={lines} />
    </div>
  )
}
