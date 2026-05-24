import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
  Cell,
} from 'recharts'
import type { MetricsResponse, TreatmentDurationRow } from '../../types'

const OUTCOME_COLORS: Record<string, string> = {
  'Complete Response': '#0d9488',
  'Very Good Partial Response': '#0891b2',
  'Partial Response': '#2563eb',
  'Minimal Response': '#7c3aed',
  'Stable Disease': '#d97706',
  'Progressive Disease': '#dc2626',
}

function shortName(name: string): string {
  return name.split(' (')[0]
}

interface Props {
  data: MetricsResponse['treatment_duration']
}

function DurationChart({ rows }: { rows: TreatmentDurationRow[] }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data
      </div>
    )
  }

  // Top 15 by count
  const top = rows
    .slice()
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)
    .map((r) => ({
      name: `${shortName(r.therapy)} / ${r.outcome}`,
      median: r.median_months,
      count: r.count,
      fill: OUTCOME_COLORS[r.outcome] ?? '#0d9488',
    }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, top.length * 36)}>
      <BarChart
        data={top}
        layout="vertical"
        margin={{ top: 4, right: 60, left: 8, bottom: 4 }}
      >
        <XAxis
          type="number"
          tick={{ fontSize: 11 }}
          label={{ value: 'Months', position: 'insideRight', offset: -4, fontSize: 11 }}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fontSize: 10 }}
          width={200}
        />
        <Tooltip
          contentStyle={{ fontSize: 12 }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={((v: unknown, _n: unknown, e: { payload?: { count?: number } }) => [
            `${Number(v).toFixed(1)} mo (n=${e.payload?.count ?? ''})`,
            'Median Duration',
          ]) as any}
        />
        <Bar dataKey="median" radius={[0, 3, 3, 0]}>
          {top.map((entry, idx) => (
            <Cell key={idx} fill={entry.fill} />
          ))}
          <LabelList
            dataKey="median"
            position="right"
            style={{ fontSize: 10, fill: '#374151' }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown) => `${Number(v).toFixed(1)}mo`) as any}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function TreatmentDuration({ data }: Props) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  // Combine all lines
  const allRows = [
    ...(data.first_line ?? []),
    ...(data.second_line ?? []),
    ...(data.later_line ?? []),
  ]

  const ttft = data.time_to_first_treatment
  const hasDistrib = ttft?.distribution && ttft.distribution.length > 0

  return (
    <div className="space-y-6">
      {/* Median duration by therapy/outcome */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Median Treatment Duration by Therapy &amp; Outcome (Top 15)
        </p>
        <DurationChart rows={allRows} />
      </div>

      {/* Time to first treatment */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Time to First Treatment Distribution
          {ttft?.median_days != null && (
            <span className="ml-2 font-normal normal-case text-gray-500">
              (Median: {ttft.median_days} days)
            </span>
          )}
        </p>
        {hasDistrib ? (
          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={ttft.distribution}
              margin={{ top: 4, right: 8, left: 0, bottom: 20 }}
            >
              <XAxis
                dataKey="bucket"
                tick={{ fontSize: 10 }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#0891b2" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
            No data
          </div>
        )}
      </div>
    </div>
  )
}
