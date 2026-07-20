import type { MetricsResponse } from '../../types'
import KMGroupChart from './KMGroupChart'

type Pod24Data = NonNullable<MetricsResponse['pod24']>

interface Props {
  data: Pod24Data
}

function PValueBadge({ p }: { p: number | null | undefined }) {
  if (p == null) return null
  const label = p < 0.001 ? 'p < 0.001' : p < 0.05 ? `p = ${p.toFixed(3)}` : `p = ${p.toFixed(2)}`
  return (
    <span className="inline-flex items-center rounded-full bg-gray-100 border border-gray-200 px-2.5 py-0.5 text-xs font-medium text-gray-600">
      {label}
    </span>
  )
}

export default function Pod24({ data }: Props) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const evaluable = data.groups.filter((g) => g.key !== 'unevaluable')
  const unevaluable = data.groups.find((g) => g.key === 'unevaluable')

  return (
    <div>
      {/* Group counts */}
      <div className="flex flex-wrap gap-4 mb-4">
        {evaluable.map((g) => (
          <div
            key={g.key}
            className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm min-w-[140px]"
          >
            <div className="text-xs font-medium text-gray-500 mb-1">{g.label}</div>
            <div className="text-2xl font-bold text-gray-900">{g.count.toLocaleString()}</div>
            <div className="text-xs text-gray-400">{g.pct.toFixed(1)}% of cohort</div>
          </div>
        ))}
        {unevaluable && (
          <div className="rounded-lg border border-dashed border-gray-200 px-4 py-3 min-w-[140px]">
            <div className="text-xs font-medium text-gray-400 mb-1">{unevaluable.label}</div>
            <div className="text-2xl font-bold text-gray-400">{unevaluable.count.toLocaleString()}</div>
          </div>
        )}
        <div className="flex items-center">
          <PValueBadge p={data.os_p} />
        </div>
      </div>

      <KMGroupChart lines={data.os} xLabel="Months from 24-month landmark" />

      <p className="text-xs text-gray-400 mt-2">
        POD24 = progression (or death, or start of next-line therapy as a progression surrogate)
        within {data.window_months} months of first-line treatment start. Clock starts at
        first-line treatment start. Patients censored before {data.window_months} months with no
        event are unevaluable. Overall survival is compared from the {data.landmark_months}-month
        landmark — only patients alive and in follow-up at {data.landmark_months} months are
        included, because the no-POD24 group cannot by definition have deaths before that point
        and a comparison from time zero would measure the classification rule rather than
        survival. Legend n = patients in the landmark analysis.
      </p>
    </div>
  )
}
