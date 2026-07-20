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

type LandmarkResponseData = NonNullable<MetricsResponse['landmark_response']>

interface Props {
  data: LandmarkResponseData
}

export default function LandmarkResponse({ data }: Props) {
  // Skip landmarks with no evaluable patients — a 0-height "0.0%" bar would
  // read as "0% response" rather than "no data".
  const landmarks = (data?.landmarks ?? []).filter((l) => l.evaluable > 0)

  if (!data || landmarks.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const clockLabel =
    data.clock_start === 'first_line_start_date'
      ? 'first-line treatment start'
      : data.clock_start

  const chartData = landmarks.map((l) => ({
    name: `CR${l.months}`,
    pct: l.pct,
    label: `${l.pct.toFixed(1)}%`,
  }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={chartData} margin={{ top: 16, right: 24, left: 0, bottom: 4 }}>
          <XAxis dataKey="name" tick={{ fontSize: 11 }} />
          <YAxis
            domain={[0, 100]}
            tickFormatter={(v: number) => `${v}%`}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={((v: unknown) => [`${Number(v).toFixed(1)}%`, 'Complete response']) as any}
          />
          <Bar dataKey="pct" fill="#0d9488" radius={[3, 3, 0, 0]}>
            <LabelList dataKey="label" position="top" style={{ fontSize: 11, fill: '#374151' }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex flex-wrap gap-4 mt-2">
        {landmarks.map((l) => (
          <span key={l.months} className="text-xs text-gray-500">
            <span className="font-semibold">CR{l.months}</span>: {l.cr_count}/{l.evaluable} evaluable
          </span>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-2">
        Proportion of evaluable first-line patients in complete response within each landmark
        (months). Clock starts at {clockLabel}. Evaluable = first-line end date
        known, the patient has died (outcome final), or follow-up reaches the landmark.
      </p>
    </div>
  )
}
