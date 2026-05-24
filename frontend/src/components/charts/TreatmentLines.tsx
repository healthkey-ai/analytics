import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'

const CHART_COLORS = [
  '#0d9488',
  '#0891b2',
  '#2563eb',
  '#7c3aed',
  '#d97706',
  '#dc2626',
  '#059669',
  '#0284c7',
]

interface FunnelRow {
  line: number
  label: string
  count: number
  pct: number
}

interface DistributionRow {
  lines: number
  label: string
  count: number
  pct: number
}

interface Props {
  funnel: FunnelRow[]
  distribution: DistributionRow[]
}

export default function TreatmentLines({ funnel, distribution }: Props) {
  const hasFunnel = funnel && funnel.length > 0
  const hasDist = distribution && distribution.length > 0

  if (!hasFunnel && !hasDist) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Left: Funnel */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Patients Reaching Each Line
        </p>
        {hasFunnel ? (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={funnel}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 4, bottom: 4 }}
            >
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 11 }}
                tickFormatter={(v: number) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="label"
                tick={{ fontSize: 11 }}
                width={40}
              />
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter={((v: unknown) => [`${Number(v).toFixed(1)}%`, 'Patients']) as any}
              />
              <Bar dataKey="pct" fill="#0d9488" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            No data
          </div>
        )}
      </div>

      {/* Right: Distribution donut */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Lines of Therapy Distribution
        </p>
        {hasDist ? (
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={distribution}
                dataKey="count"
                nameKey="label"
                cx="50%"
                cy="45%"
                innerRadius={45}
                outerRadius={80}
                paddingAngle={2}
              >
                {distribution.map((_, idx) => (
                  <Cell
                    key={idx}
                    fill={CHART_COLORS[idx % CHART_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter={((v: unknown) => [v, '']) as any}
              />
              <Legend
                wrapperStyle={{ fontSize: 11 }}
                formatter={(value: string) => value}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            No data
          </div>
        )}
      </div>
    </div>
  )
}
