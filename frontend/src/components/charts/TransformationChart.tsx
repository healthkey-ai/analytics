import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { MetricsResponse } from '../../types'
import KMGroupChart from './KMGroupChart'

type TransformationData = NonNullable<MetricsResponse['transformation']>

interface Props {
  data: TransformationData
}

const OUTCOME_COLORS: Record<string, string> = {
  CR: '#059669',
  PR: '#0d9488',
  SD: '#d97706',
  PD: '#dc2626',
  Deceased: '#374151',
  Unknown: '#9ca3af',
}

export default function TransformationChart({ data }: Props) {
  if (!data || data.evaluable === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const ttt = data.time_to_transformation
  const outcomeData = data.outcome_distribution.map((o) => ({
    name: o.outcome,
    count: o.count,
    pct: o.pct,
    label: `${o.count} (${o.pct.toFixed(1)}%)`,
    fill: OUTCOME_COLORS[o.outcome] ?? '#9ca3af',
  }))

  const osLine = { label: 'Post-transformation OS', ...data.os_post_transformation }

  return (
    <div>
      {/* Summary tiles */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm min-w-[150px]">
          <div className="text-xs font-medium text-gray-500 mb-1">Transformed to DLBCL</div>
          <div className="text-2xl font-bold text-gray-900">{data.transformed_count.toLocaleString()}</div>
          <div className="text-xs text-gray-400">{data.transformed_pct.toFixed(1)}% of {data.evaluable.toLocaleString()} evaluable</div>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 shadow-sm min-w-[150px]">
          <div className="text-xs font-medium text-gray-500 mb-1">Median time to transformation</div>
          <div className="text-2xl font-bold text-gray-900">
            {ttt.median_months != null ? `${ttt.median_months.toFixed(1)} mo` : '—'}
          </div>
          <div className="text-xs text-gray-400">from diagnosis · n={ttt.n}</div>
        </div>
        {data.unknown > 0 && (
          <div className="rounded-lg border border-dashed border-gray-200 px-4 py-3 min-w-[150px]">
            <div className="text-xs font-medium text-gray-400 mb-1">Not documented</div>
            <div className="text-2xl font-bold text-gray-400">{data.unknown.toLocaleString()}</div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* When — histogram */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Time from diagnosis to transformation (months)
          </h3>
          {ttt.n === 0 ? (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">No dated transformations</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ttt.histogram} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={((v: unknown) => [v, 'Patients']) as any}
                />
                <Bar dataKey="count" fill="#0d9488" radius={[3, 3, 0, 0]}>
                  <LabelList dataKey="count" position="top" style={{ fontSize: 11, fill: '#374151' }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* How — outcome distribution */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Outcome after transformation</h3>
          {outcomeData.length === 0 ? (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">No transformed patients</div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={outcomeData} layout="vertical" margin={{ top: 4, right: 80, left: 8, bottom: 4 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={80} />
                <Tooltip
                  contentStyle={{ fontSize: 12 }}
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  formatter={((v: unknown) => [v, 'Patients']) as any}
                />
                <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                  {outcomeData.map((d) => (
                    <Cell key={d.name} fill={d.fill} />
                  ))}
                  <LabelList dataKey="label" position="right" style={{ fontSize: 11, fill: '#374151' }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* OS after transformation */}
      {data.os_post_transformation.n > 0 && (
        <div className="mt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Overall survival after transformation</h3>
          <KMGroupChart lines={[osLine]} xLabel="Months from transformation" />
        </div>
      )}

      <p className="text-xs text-gray-400 mt-4">
        Shown only where a transformation is documented. Not every patient is biopsied at
        progression, so some who behave as though they have transformed are never confirmed —
        the true transformation rate may be higher.
      </p>
    </div>
  )
}
