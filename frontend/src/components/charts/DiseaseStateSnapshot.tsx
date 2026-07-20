import type { MetricsResponse } from '../../types'

type DiseaseStateData = NonNullable<MetricsResponse['disease_state']>

interface Props {
  data: DiseaseStateData
}

const STATE_STYLES: Record<string, { dot: string }> = {
  newly_diagnosed:     { dot: 'bg-sky-500' },
  watch_and_wait:      { dot: 'bg-amber-500' },
  in_remission:        { dot: 'bg-emerald-500' },
  relapsed_refractory: { dot: 'bg-rose-500' },
  other:               { dot: 'bg-gray-400' },
}

export default function DiseaseStateSnapshot({ data }: Props) {
  if (!data || data.total === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
      {data.states.map((s) => (
        <div
          key={s.key}
          className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className={`inline-block h-2.5 w-2.5 rounded-full ${STATE_STYLES[s.key]?.dot ?? 'bg-gray-400'}`} />
            <span className="text-xs font-medium text-gray-500">{s.label}</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{s.count.toLocaleString()}</div>
          <div className="text-xs text-gray-400">{s.pct.toFixed(1)}% of cohort</div>
        </div>
      ))}
    </div>
  )
}
