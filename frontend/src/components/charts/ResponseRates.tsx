import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { TherapyOutcomes } from '../../types'

const OUTCOME_COLORS: Record<string, string> = {
  'Complete Response': '#0d9488',
  'Very Good Partial Response': '#0891b2',
  'Partial Response': '#2563eb',
  'Minimal Response': '#7c3aed',
  'Stable Disease': '#d97706',
  'Progressive Disease': '#dc2626',
}

const OUTCOME_ORDER = [
  'Complete Response',
  'Very Good Partial Response',
  'Partial Response',
  'Minimal Response',
  'Stable Disease',
  'Progressive Disease',
]

interface Props {
  data: TherapyOutcomes[]
  title: string
}

type ViewMode = 'chart' | 'table'

function shortName(name: string): string {
  return name.split(' (')[0]
}

export default function ResponseRates({ data, title }: Props) {
  const [view, setView] = useState<ViewMode>('chart')

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  // Collect all outcomes present in data
  const presentOutcomes = OUTCOME_ORDER.filter((o) =>
    data.some((row) => (row.outcomes[o] ?? 0) > 0)
  )

  // Build chart data rows
  const chartData = data.map((row) => {
    const entry: Record<string, string | number> = {
      name: shortName(row.therapy),
    }
    for (const o of presentOutcomes) {
      entry[o] = row.outcomes[o] ?? 0
    }
    return entry
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-gray-700">{title}</span>
        <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50">
          {(['chart', 'table'] as ViewMode[]).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              className={`px-3 py-1 text-xs rounded-md font-medium transition-colors ${
                view === v
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {v.charAt(0).toUpperCase() + v.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {view === 'chart' ? (
        <ResponsiveContainer width="100%" height={Math.max(200, data.length * 44)}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
          >
            <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11 }}
              width={130}
            />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={((v: unknown, n: unknown) => [v, n]) as any}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {presentOutcomes.map((outcome) => (
              <Bar key={outcome} dataKey={outcome} stackId="a" fill={OUTCOME_COLORS[outcome]}>
                {chartData.map((_, idx) => (
                  <Cell key={idx} fill={OUTCOME_COLORS[outcome]} />
                ))}
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-collapse">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-2 px-3 font-semibold text-gray-600">Therapy</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-600">n</th>
                <th className="text-right py-2 px-3 font-semibold text-gray-600">ORR%</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr
                  key={i}
                  className={`border-b border-gray-100 ${i % 2 === 0 ? '' : 'bg-gray-50'}`}
                >
                  <td className="py-2 px-3 text-gray-800">{shortName(row.therapy)}</td>
                  <td className="py-2 px-3 text-right text-gray-700">{row.total}</td>
                  <td className="py-2 px-3 text-right font-medium text-teal-700">
                    {row.orr_pct.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
