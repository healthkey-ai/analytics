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

interface Props {
  data: MetricsResponse['ttnt']
}

const LINE_CONFIG = [
  { key: 'line_1_to_2', label: '1L → 2L', color: '#0d9488' },
  { key: 'line_2_to_3', label: '2L → 3L', color: '#7c3aed' },
] as const

function mergeKMCurves(data: MetricsResponse['ttnt']) {
  const allTimes = [
    ...new Set(
      LINE_CONFIG.flatMap(({ key }) => data[key].curve.map((p) => p.time))
    ),
  ].sort((a, b) => a - b)

  return allTimes.map((time) => {
    const point: Record<string, number> = { time }
    LINE_CONFIG.forEach(({ key }) => {
      const curve = data[key].curve
      const last  = [...curve].reverse().find((p) => p.time <= time)
      point[key]  = last ? last.survival : 1.0
    })
    return point
  })
}

export default function TTNT({ data }: Props) {
  if (!data) return null

  const hasAny = LINE_CONFIG.some(({ key }) => data[key].curve.length > 1)
  if (!hasAny) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const chartData = mergeKMCurves(data)

  return (
    <div>
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

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 4, right: 24, left: 0, bottom: 24 }}>
          <XAxis
            dataKey="time"
            type="number"
            label={{ value: 'Months after end of prior line', position: 'insideBottom', offset: -12, fontSize: 11 }}
            tick={{ fontSize: 11 }}
            domain={[0, 'auto']}
          />
          <YAxis
            domain={[0, 1]}
            tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
            tick={{ fontSize: 11 }}
            label={{ value: '% not yet on next line', angle: -90, position: 'insideLeft', fontSize: 11, offset: 10 }}
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
        Time from end of current line to start of next line. Event = initiation of next therapy.
        Patients without a subsequent line are censored at last contact. Dashed line = 50% (median reference).
      </p>
    </div>
  )
}
