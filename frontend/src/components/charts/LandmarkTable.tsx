import type { SubgroupSurvivalLine } from '../../types'

const COLORS = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed']

interface Props {
  lines: SubgroupSurvivalLine[]
  landmarks?: number[]
}

function survivalAt(
  curve: SubgroupSurvivalLine['curve'],
  t: number
): number {
  const last = [...curve].reverse().find((p) => p.time <= t)
  return last ? last.survival : 1.0
}

export default function LandmarkTable({ lines, landmarks = [6, 12, 24, 36] }: Props) {
  if (!lines || lines.length === 0) return null

  return (
    <div className="mt-4 overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2 pr-4 font-semibold text-gray-600">Group</th>
            <th className="text-right py-2 px-2 font-semibold text-gray-600">n</th>
            {landmarks.map((t) => (
              <th key={t} className="text-right py-2 px-2 font-semibold text-gray-600">
                {t} mo
              </th>
            ))}
            <th className="text-right py-2 pl-2 font-semibold text-gray-600">Median</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line, i) => (
            <tr key={line.label} className="border-b border-gray-100">
              <td className="py-1.5 pr-4">
                <span className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-2 h-2 rounded-full flex-shrink-0"
                    style={{ backgroundColor: COLORS[i % COLORS.length] }}
                  />
                  <span className="text-gray-700">{line.label}</span>
                </span>
              </td>
              <td className="text-right py-1.5 px-2 text-gray-600">{line.n}</td>
              {landmarks.map((t) => (
                <td key={t} className="text-right py-1.5 px-2 text-gray-700">
                  {(survivalAt(line.curve, t) * 100).toFixed(1)}%
                </td>
              ))}
              <td className="text-right py-1.5 pl-2 text-gray-700">
                {line.median != null ? `${line.median.toFixed(1)} mo` : 'NR'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
