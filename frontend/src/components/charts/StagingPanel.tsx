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
  data: MetricsResponse['staging']
}

function NoData() {
  return (
    <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
      No data
    </div>
  )
}

export default function StagingPanel({ data }: Props) {
  if (!data) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  const hasCrab = data.crab && data.crab.length > 0
  const hasBone = data.bone_lesions && data.bone_lesions.length > 0

  return (
    <div className="grid grid-cols-2 gap-6">
      {/* ISS Stage distribution */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          ISS Stage Distribution
        </p>
        {data.stages && data.stages.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={data.stages}
                dataKey="count"
                nameKey="stage"
                cx="50%"
                cy="45%"
                innerRadius={40}
                outerRadius={70}
                paddingAngle={3}
              >
                {data.stages.map((_, idx) => (
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

      {/* ECOG distribution */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          ECOG Performance Status
        </p>
        {data.ecog && data.ecog.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart
              data={data.ecog.map((e) => ({ name: `ECOG ${e.ecog}`, count: e.count }))}
              margin={{ top: 4, right: 8, left: 0, bottom: 4 }}
            >
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#7c3aed" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
      </div>

      {/* Cytogenetics horizontal bar */}
      <div className="col-span-2">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Cytogenetic Markers
        </p>
        {data.cytogenetics && data.cytogenetics.length > 0 ? (
          <ResponsiveContainer
            width="100%"
            height={Math.max(160, data.cytogenetics.length * 34)}
          >
            <BarChart
              data={data.cytogenetics.map((c) => ({
                name: c.marker,
                count: c.count,
                high_risk: c.high_risk,
              }))}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
            >
              <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 10 }}
                width={140}
              />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" radius={[0, 3, 3, 0]}>
                {data.cytogenetics.map((entry, idx) => (
                  <Cell
                    key={idx}
                    fill={entry.high_risk ? '#dc2626' : '#9ca3af'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <NoData />
        )}
        <p className="text-xs text-gray-400 mt-1">
          <span className="inline-block w-3 h-3 rounded-sm bg-red-600 mr-1 align-middle" />
          High-risk
          <span className="inline-block w-3 h-3 rounded-sm bg-gray-400 mx-1 ml-3 align-middle" />
          Standard risk
        </p>
      </div>

      {/* CRAB criteria */}
      {hasCrab && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            CRAB Criteria
          </p>
          <ResponsiveContainer
            width="100%"
            height={Math.max(120, data.crab.length * 40)}
          >
            <BarChart
              data={data.crab}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
            >
              <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="label"
                tick={{ fontSize: 10 }}
                width={80}
              />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#d97706" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Bone lesions */}
      {hasBone && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Bone Lesions
          </p>
          <ResponsiveContainer
            width="100%"
            height={Math.max(120, data.bone_lesions.length * 40)}
          >
            <BarChart
              data={data.bone_lesions}
              layout="vertical"
              margin={{ top: 4, right: 48, left: 8, bottom: 4 }}
            >
              <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="type"
                tick={{ fontSize: 10 }}
                width={100}
              />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#0891b2" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* SCT stat */}
      <div className={hasCrab || hasBone ? '' : 'col-span-2'}>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
          Stem Cell Transplant
        </p>
        <div className="flex items-center gap-4 p-4 bg-teal-50 rounded-lg border border-teal-100">
          <div className="text-3xl font-bold text-teal-700">
            {data.sct_pct != null ? `${data.sct_pct.toFixed(1)}%` : 'N/A'}
          </div>
          <div>
            <p className="text-sm font-medium text-teal-900">Received ASCT</p>
            {data.sct_count != null && (
              <p className="text-xs text-teal-600">{data.sct_count} patients</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
