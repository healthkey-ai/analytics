import type { LabStats } from '../../types'

const LAB_ORDER = [
  'hemoglobin',
  'beta2_microglobulin',
  'albumin',
  'creatinine',
  'ldh',
  'm_protein',
  'calcium',
]

interface Props {
  data: Record<string, LabStats>
}

interface BoxPlotBarProps {
  stat: LabStats
}

function BoxPlotBar({ stat }: BoxPlotBarProps) {
  const { min, q1, median, q3, max, unit, label, n } = stat
  const range = max - min || 1
  const toPercent = (v: number) => ((v - min) / range) * 100

  const q1Pct = toPercent(q1)
  const q3Pct = toPercent(q3)
  const medianPct = toPercent(median)
  const boxWidth = q3Pct - q1Pct

  return (
    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-semibold text-gray-700">{label}</span>
        <span className="text-xs text-gray-400">n={n}</span>
      </div>
      <div className="text-sm font-bold text-teal-700 mb-2">
        {median.toFixed(1)}{' '}
        <span className="text-xs font-normal text-gray-500">{unit}</span>
      </div>

      {/* Box plot */}
      <div className="relative h-6 flex items-center">
        {/* Track */}
        <div className="absolute inset-y-2 left-0 right-0 bg-gray-200 rounded-full" />

        {/* Min whisker */}
        <div
          className="absolute top-1 bottom-1 w-0.5 bg-gray-400"
          style={{ left: `${toPercent(min)}%` }}
        />
        {/* Whisker line min→Q1 */}
        <div
          className="absolute top-1/2 h-0.5 bg-gray-400"
          style={{
            left: `${toPercent(min)}%`,
            width: `${q1Pct - toPercent(min)}%`,
          }}
        />

        {/* IQR box */}
        <div
          className="absolute top-1 bottom-1 bg-teal-400 rounded-sm opacity-80"
          style={{ left: `${q1Pct}%`, width: `${Math.max(boxWidth, 1)}%` }}
        />

        {/* Median marker */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-teal-800"
          style={{ left: `${medianPct}%` }}
        />

        {/* Whisker line Q3→max */}
        <div
          className="absolute top-1/2 h-0.5 bg-gray-400"
          style={{
            left: `${q3Pct}%`,
            width: `${toPercent(max) - q3Pct}%`,
          }}
        />
        {/* Max whisker */}
        <div
          className="absolute top-1 bottom-1 w-0.5 bg-gray-400"
          style={{ left: `${toPercent(max)}%` }}
        />
      </div>

      {/* Axis labels */}
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-400">{min.toFixed(1)}</span>
        <span className="text-xs text-gray-500">
          Q1 {q1.toFixed(1)} – Q3 {q3.toFixed(1)}
        </span>
        <span className="text-xs text-gray-400">{max.toFixed(1)}</span>
      </div>
    </div>
  )
}

export default function LabsPanel({ data }: Props) {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  // Show labs in preferred order, then any extras
  const orderedKeys = [
    ...LAB_ORDER.filter((k) => k in data),
    ...Object.keys(data).filter((k) => !LAB_ORDER.includes(k)),
  ]

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
      {orderedKeys.map((key) => (
        <BoxPlotBar key={key} stat={data[key]} />
      ))}
    </div>
  )
}
