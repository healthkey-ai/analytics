import type { MetricsResponse } from '../../types'
import KMGroupChart from './KMGroupChart'

type PathwayOutcomesData = NonNullable<MetricsResponse['pathway_outcomes']>

interface Props {
  data: PathwayOutcomesData
}

export default function PathwayOutcomes({ data }: Props) {
  const pathways = data?.pathways ?? []

  if (pathways.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No treatment pathways with enough patients to compare
      </div>
    )
  }

  const lines = pathways.map((p) => ({ label: p.label, ...p.os }))

  return (
    <div>
      <KMGroupChart lines={lines} />
      <p className="text-xs text-gray-400 mt-2">
        Overall survival from first-line start for the most common 1L → 2L pathway combinations.
        Only pathways with at least {data.min_n} patients are shown; small pathways are unreliable.
      </p>
    </div>
  )
}
