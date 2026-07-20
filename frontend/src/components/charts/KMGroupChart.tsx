import { useMemo } from 'react'
import type { ReactNode } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { mergeKMCurves } from '../../utils/kmChartUtils'
import type { SubgroupSurvivalLine } from '../../types'

interface Props {
  lines: SubgroupSurvivalLine[]
  xLabel?: string
  /** Optional content appended to the legend row (e.g. a p-value badge). */
  legendExtra?: ReactNode
}

const COLORS = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed']

/**
 * Shared Kaplan-Meier step chart for a set of labelled survival lines.
 * Lines with no curve points are dropped — otherwise mergeKMCurves would
 * forward-fill them to a phantom flat line at 100% survival.
 */
export default function KMGroupChart({ lines, xLabel = 'Months from 1st-line start', legendExtra }: Props) {
  const validLines = useMemo(
    () => (lines ?? []).filter((l) => l.curve && l.curve.length > 0),
    [lines]
  )

  const chartData = useMemo(
    () => mergeKMCurves(validLines.map((l, i) => ({ key: `g${i}`, curve: l.curve }))),
    [validLines]
  )

  if (validLines.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  return (
    <div>
      {/* Legend */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <div className="flex flex-wrap gap-6">
          {validLines.map((line, i) => (
            <div key={line.label} className="flex items-center gap-2">
              <span className="inline-block w-8 h-0.5" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
              <span className="text-xs text-gray-600">
                <span className="font-semibold">{line.label}</span>
                {' · n='}{line.n}
                {line.median != null
                  ? ` · median ${line.median.toFixed(1)} mo`
                  : ' · median NR'}
              </span>
            </div>
          ))}
        </div>
        {legendExtra}
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 4, right: 24, left: 0, bottom: 24 }}>
          <XAxis
            dataKey="time"
            type="number"
            label={{ value: xLabel, position: 'insideBottom', offset: -12, fontSize: 11 }}
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
            formatter={(v: unknown, name: unknown) => {
              const nameStr = String(name)
              if (nameStr.endsWith('_lower') || nameStr.endsWith('_upper')) return null
              const idx = Number(nameStr.replace('g', ''))
              const label = validLines[idx]?.label ?? nameStr
              return [`${(Number(v) * 100).toFixed(1)}%`, label]
            }}
            labelFormatter={(t: unknown) => `${Number(t)} months`}
            contentStyle={{ fontSize: 12 }}
          />
          <ReferenceLine y={0.5} stroke="#9ca3af" strokeDasharray="4 4" />
          {validLines.map((line, i) => (
            <Line
              key={line.label}
              type="stepAfter"
              dataKey={`g${i}`}
              name={`g${i}`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          ))}
          {/* CI bands — dashed, low opacity, excluded from legend/tooltip */}
          {validLines.map((line, i) => [
            <Line
              key={`${line.label}_lower`}
              type="stepAfter"
              dataKey={`g${i}_lower`}
              name={`g${i}_lower`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={1}
              strokeOpacity={0.3}
              strokeDasharray="3 3"
              dot={false}
              legendType="none"
            />,
            <Line
              key={`${line.label}_upper`}
              type="stepAfter"
              dataKey={`g${i}_upper`}
              name={`g${i}_upper`}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={1}
              strokeOpacity={0.3}
              strokeDasharray="3 3"
              dot={false}
              legendType="none"
            />,
          ])}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
