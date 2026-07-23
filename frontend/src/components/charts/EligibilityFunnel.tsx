import type { MetricsResponse } from '../../types'

type EligibilityData = NonNullable<MetricsResponse['eligibility']>

interface Props {
  data: EligibilityData
}

export default function EligibilityFunnel({ data }: Props) {
  if (data.total === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  if (data.steps.length <= 1) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm text-center px-6">
        No cohort filters applied — set filters in the cohort panel to size an eligibility profile.
      </div>
    )
  }

  return (
    <div>
      <div className="mb-4">
        <span className="text-3xl font-bold text-gray-900">{data.eligible.toLocaleString()}</span>
        <span className="ml-2 text-sm text-gray-500">
          eligible ({data.eligible_pct.toFixed(1)}% of {data.total.toLocaleString()} patients)
        </span>
      </div>
      <div className="space-y-2">
        {data.steps.map((step, i) => {
          const pct = (step.count / data.total) * 100
          const isLast = i === data.steps.length - 1
          return (
            <div key={step.key}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="font-medium text-gray-600">{step.label}</span>
                <span className="text-gray-500">
                  {step.count.toLocaleString()} · {pct.toFixed(1)}%
                </span>
              </div>
              <div className="h-5 w-full rounded bg-gray-100">
                <div
                  className={`h-5 rounded ${isLast ? 'bg-teal-600' : 'bg-teal-300'}`}
                  style={{ width: `${Math.max(pct, 0.5)}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
