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

interface Props {
  data: MetricsResponse['survival']
}

const LINE_CONFIG = [
  { key: 'os',  label: 'OS',  color: '#2563eb' },
  { key: 'pfs', label: 'PFS', color: '#0d9488' },
  { key: 'efs', label: 'EFS', color: '#d97706' },
] as const

export default function SurvivalCurves({ data }: Props) {
  if (!data) return null

  const hasAny = LINE_CONFIG.some(({ key }) => data[key].curve.length > 1)
  if (!hasAny) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const chartData = mergeKMCurves(LINE_CONFIG.map(({ key }) => ({ key, curve: data[key].curve })))

  return (
    <div>
      {/* Summary row */}
      <div className="flex flex-wrap gap-6 mb-4">
        {LINE_CONFIG.map(({ key, label, color }) => {
          const line = data[key]
          return line.n > 0 ? (
            <div key={key} className="flex items-center gap-2">
              <span className="inline-block w-8 h-0.5" style={{ backgroundColor: color }} />
              <span className="text-xs text-gray-600">
                <span className="font-semibold">{label}</span>
                {' · n='}
                {line.n}
                {line.median != null
                  ? ` · median ${line.median.toFixed(1)} mo`
                  : ' · median not reached'}
              </span>
            </div>
          ) : null
        })}
      </div>

      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={chartData} margin={{ top: 4, right: 24, left: 0, bottom: 24 }}>
          <XAxis
            dataKey="time"
            type="number"
            label={{ value: 'Months from 1st-line start', position: 'insideBottom', offset: -12, fontSize: 11 }}
            tick={{ fontSize: 11 }}
            domain={[0, 'auto']}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fontSize: 11 }}
            label={{ value: 'Survival probability', angle: -90, position: 'insideLeft', fontSize: 11, offset: 10 }}
          />
          <Tooltip
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown) => [`${(Number(v) * 100).toFixed(1)}%`]) as any}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            labelFormatter={((t: number) => `${t} months`) as any}
            contentStyle={{ fontSize: 12 }}
          />
          <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" />
          {LINE_CONFIG.map(({ key, label, color }) =>
            data[key].n > 0 ? (
              <Line
                key={key}
                type="stepAfter"
                dataKey={key}
                name={label}
                stroke={color}
                strokeWidth={2}
                dot={false}
                connectNulls
              />
            ) : null
          )}
        </LineChart>
      </ResponsiveContainer>

      <p className="text-xs text-gray-400 mt-2">
        <span className="font-medium text-blue-600">OS</span>: 1L start → death. &nbsp;
        <span className="font-medium text-teal-600">PFS</span>: 1L start → first progression (any line) or death. &nbsp;
        <span className="font-medium text-amber-600">EFS</span>: 1L start → treatment change, progression, or death. &nbsp;
        Patients without an event are censored at last known contact. Dashed line = 50% (median reference).
      </p>
    </div>
  )
}
