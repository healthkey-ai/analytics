import { useState, useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import type { MetricsResponse } from '../../types'
import { mergeKMCurves } from '../../utils/kmChartUtils'

type DORData = NonNullable<MetricsResponse['dor']>
type LineKey = 'first_line' | 'second_line'

interface Props {
  data: DORData
}

const LINE_CONFIG: { key: LineKey; label: string; color: string }[] = [
  { key: 'first_line',  label: '1st Line', color: '#0d9488' },
  { key: 'second_line', label: '2nd Line', color: '#7c3aed' },
]

export default function DurationOfResponse({ data }: Props) {
  const [activeLine, setActiveLine] = useState<LineKey>('first_line')

  const line   = data[activeLine]
  const config = LINE_CONFIG.find((c) => c.key === activeLine)!

  const toggleClass = (active: boolean) =>
    `px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
      active ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
    }`

  const chartData = useMemo(
    () => mergeKMCurves([{ key: 'dor', curve: line.curve }]),
    [line]
  )

  if (!line || line.n === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  return (
    <div>
      {/* Line toggle */}
      <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-4">
        {LINE_CONFIG.map(({ key, label }) => (
          <button key={key} onClick={() => setActiveLine(key)} className={toggleClass(activeLine === key)}>
            {label}
          </button>
        ))}
      </div>

      {/* Legend / stats */}
      <div className="flex items-center gap-2 mb-4">
        <span className="inline-block w-8 h-0.5" style={{ backgroundColor: config.color }} />
        <span className="text-xs text-gray-600">
          <span className="font-semibold">{config.label}</span>
          {' · n='}{line.n}
          {line.median != null
            ? ` · median ${line.median.toFixed(1)} mo`
            : ' · median NR'}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 4, right: 24, left: 0, bottom: 24 }}>
          <XAxis
            dataKey="time"
            type="number"
            label={{ value: 'Months from line start (responders)', position: 'insideBottom', offset: -12, fontSize: 11 }}
            tick={{ fontSize: 11 }}
            domain={[0, 'auto']}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fontSize: 11 }}
            label={{ value: 'Probability of ongoing response', angle: -90, position: 'insideLeft', fontSize: 11, offset: 10 }}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown) => [`${(Number(v) * 100).toFixed(1)}%`, config.label]) as any}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={((t: number) => `${t} months`) as any}
            contentStyle={{ fontSize: 12 }}
          />
          <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" />
          <Line
            type="stepAfter"
            dataKey="dor"
            name="dor"
            stroke={config.color}
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-400 mt-2">
        DOR: 1L/2L start → next treatment or death, among responders.
        Stable disease / progression excluded.
      </p>
    </div>
  )
}
