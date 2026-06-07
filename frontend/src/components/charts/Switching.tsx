import { useState } from 'react'
import type { MetricsResponse } from '../../types'

interface Props {
  data: MetricsResponse['switching']
}

// Stable color palette for up to 12 destination regimens
const COLORS = [
  '#0d9488', '#2563eb', '#d97706', '#7c3aed', '#dc2626',
  '#059669', '#db2777', '#ea580c', '#0891b2', '#65a30d',
  '#9333ea', '#6b7280',
]

type LineKey = 'from_1l' | 'from_2l'

export default function Switching({ data }: Props) {
  const [line, setLine] = useState<LineKey>('from_1l')

  const rows = data?.[line] ?? []

  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        No data available
      </div>
    )
  }

  // Collect all unique destination regimens, sorted by total frequency
  const toFreq: Record<string, number> = {}
  rows.forEach(row => row.switches.forEach(s => {
    toFreq[s.to_regimen] = (toFreq[s.to_regimen] ?? 0) + s.n
  }))
  const allDests = Object.entries(toFreq)
    .sort((a, b) => b[1] - a[1])
    .map(([reg]) => reg)

  const colorMap: Record<string, string> = {}
  allDests.forEach((reg, i) => { colorMap[reg] = COLORS[i % COLORS.length] })

  // Shorten long regimen names for display
  const shorten = (name: string) =>
    name.replace(/ \(.*?\)/g, '').replace(' Monotherapy', '').trim()

  return (
    <div>
      {/* Line toggle */}
      <div className="flex gap-1 rounded-lg border border-gray-200 p-0.5 bg-gray-50 w-fit mb-5">
        {(['from_1l', 'from_2l'] as LineKey[]).map((k) => (
          <button
            key={k}
            onClick={() => setLine(k)}
            className={`px-4 py-1.5 text-xs rounded-md font-semibold transition-colors ${
              line === k ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {k === 'from_1l' ? '1L → 2L' : '2L → 3L'}
          </button>
        ))}
      </div>

      {/* Stacked bar per from-regimen */}
      <div className="space-y-3">
        {rows.map(row => (
          <div key={row.from_regimen}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-gray-700 font-medium w-52 shrink-0 truncate" title={row.from_regimen}>
                {shorten(row.from_regimen)}
              </span>
              <span className="text-xs text-gray-400">n={row.n_switched}</span>
            </div>
            <div className="flex h-6 rounded overflow-hidden w-full">
              {row.switches.map(s => (
                <div
                  key={s.to_regimen}
                  style={{ width: `${s.pct}%`, backgroundColor: colorMap[s.to_regimen] }}
                  title={`${shorten(s.to_regimen)}: ${s.n} patients (${s.pct}%)`}
                  className="flex items-center justify-center overflow-hidden"
                >
                  {s.pct >= 12 && (
                    <span className="text-white text-[10px] font-medium px-1 truncate">
                      {s.pct.toFixed(0)}%
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1">
        {allDests.map(reg => (
          <div key={reg} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm shrink-0" style={{ backgroundColor: colorMap[reg] }} />
            <span className="text-[11px] text-gray-500">{shorten(reg)}</span>
          </div>
        ))}
      </div>

      <p className="text-xs text-gray-400 mt-3">
        Only regimens with ≥2 patients who switched to a subsequent line are shown.
        Bar width = % of switchers who received each next-line regimen.
      </p>
    </div>
  )
}
