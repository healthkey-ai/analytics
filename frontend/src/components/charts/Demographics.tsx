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
import type { MetricsResponse } from '../../types'

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

interface Props {
  data: MetricsResponse['demographics']
}

export default function Demographics({ data }: Props) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const topRegions = (data.region ?? [])
    .slice()
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* Age distribution */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Age Distribution
        </p>
        {data.age_distribution && data.age_distribution.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={data.age_distribution}
              margin={{ top: 4, right: 8, left: 0, bottom: 20 }}
            >
              <XAxis
                dataKey="bucket"
                tick={{ fontSize: 10 }}
                angle={-35}
                textAnchor="end"
                interval={0}
              />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#0d9488" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
      </div>

      {/* Gender donut */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Gender
        </p>
        {data.gender && data.gender.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data.gender}
                dataKey="count"
                nameKey="gender"
                cx="50%"
                cy="45%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={3}
              >
                {data.gender.map((_, idx) => (
                  <Cell key={idx} fill={CHART_COLORS[idx % CHART_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ fontSize: 12 }}
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                formatter={((v: unknown) => [v, '']) as any}
              />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
      </div>

      {/* Ethnicity horizontal bar */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Ethnicity
        </p>
        {data.ethnicity && data.ethnicity.length > 0 ? (
          <ResponsiveContainer
            width="100%"
            height={Math.max(160, data.ethnicity.length * 32)}
          >
            <BarChart
              data={data.ethnicity}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
            >
              <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="ethnicity"
                tick={{ fontSize: 10 }}
                width={120}
              />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#0891b2" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
      </div>

      {/* Geographic top 10 */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Geographic Distribution (Top 10)
        </p>
        {topRegions.length > 0 ? (
          <ResponsiveContainer
            width="100%"
            height={Math.max(160, topRegions.length * 32)}
          >
            <BarChart
              data={topRegions}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
            >
              <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="region"
                tick={{ fontSize: 10 }}
                width={80}
              />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#2563eb" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
      </div>
    </div>
  )
}

function NoData() {
  return (
    <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
      No data
    </div>
  )
}
