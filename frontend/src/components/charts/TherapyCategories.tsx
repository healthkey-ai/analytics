import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { MetricsResponse } from '../../types'

type TherapyCategoriesData = NonNullable<MetricsResponse['therapy_categories']>

interface Props {
  data: TherapyCategoriesData
}

type LineTab = 'first_line' | 'second_line' | 'later_line'

const LINE_TABS: { key: LineTab; label: string }[] = [
  { key: 'first_line',  label: '1st Line' },
  { key: 'second_line', label: '2nd Line' },
  { key: 'later_line',  label: '3rd Line+' },
]

export default function TherapyCategories({ data }: Props) {
  const [line, setLine] = useState<LineTab>('first_line')

  const rows = data?.[line] ?? []

  if (!data || rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const chartData = rows.map((row) => ({
    name: row.category,
    count: row.count,
    pct: row.pct,
    label: `${row.count} (${row.pct.toFixed(1)}%)`,
  }))

  return (
    <div>
      <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-4">
        {LINE_TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setLine(key)}
            className={`px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
              line === key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={Math.max(200, chartData.length * 40)}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 4, right: 100, left: 8, bottom: 4 }}
        >
          <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fontSize: 11 }}
            width={150}
          />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown) => [v, 'Patients']) as any}
          />
          <Bar dataKey="count" fill="#0d9488" radius={[0, 3, 3, 0]}>
            <LabelList
              dataKey="label"
              position="right"
              style={{ fontSize: 11, fill: '#374151' }}
            />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-400 mt-2">
        Regimens can belong to more than one category (e.g. R-CHOP is both chemotherapy-containing
        and a monoclonal-antibody regimen), so percentages need not sum to 100.
      </p>
    </div>
  )
}
