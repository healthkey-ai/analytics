import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from 'recharts'

interface Props {
  sequences: { sequence: string; count: number }[]
}

export default function Sequences({ sequences }: Props) {
  if (!sequences || sequences.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const sorted = sequences
    .slice()
    .sort((a, b) => b.count - a.count)

  return (
    <ResponsiveContainer width="100%" height={Math.max(200, sorted.length * 38)}>
      <BarChart
        data={sorted}
        layout="vertical"
        margin={{ top: 4, right: 56, left: 8, bottom: 4 }}
      >
        <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="sequence"
          tick={{ fontSize: 10 }}
          width={260}
        />
        <Tooltip
          contentStyle={{ fontSize: 12 }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          formatter={((v: unknown) => [v, 'Patients']) as any}
        />
        <Bar dataKey="count" fill="#0d9488" radius={[0, 3, 3, 0]}>
          <LabelList
            dataKey="count"
            position="right"
            style={{ fontSize: 11, fill: '#374151' }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
