import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'
import type { TherapyCount } from '../../types'

interface Props {
  data: TherapyCount[]
  title: string
}

function shortName(name: string): string {
  return name.split(' (')[0]
}

export default function TreatmentPatterns({ data, title }: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const chartData = data.map((row) => ({
    name: shortName(row.therapy),
    count: row.count,
    pct: row.pct,
    label: `${row.count} (${row.pct.toFixed(1)}%)`,
  }))

  return (
    <div>
      {title && (
        <span className="text-sm font-medium text-gray-700 block mb-3">{title}</span>
      )}
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
            width={130}
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
    </div>
  )
}
