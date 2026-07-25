import { useState, useRef } from 'react'
import { useOutsideClick } from '../../hooks/useOutsideClick'

interface Props {
  title: string
  children: React.ReactNode
  className?: string
  description?: string
  onExport?: () => void | Promise<void>
}

export default function MetricCard({ title, children, className = '', description, onExport }: Props) {
  const [showExportMenu, setShowExportMenu] = useState(false)
  const exportMenuRef = useRef<HTMLDivElement>(null)
  useOutsideClick(exportMenuRef, () => setShowExportMenu(false), showExportMenu)

  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm p-5 ${className}`}>
      <div className="flex items-center gap-1.5 mb-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide flex-1">{title}</h3>
        {description && (
          <div className="relative group flex-shrink-0">
            <button
              type="button"
              className="flex items-center justify-center w-4 h-4 rounded-full bg-gray-100 text-gray-400 hover:bg-gray-200 hover:text-gray-600 text-[10px] font-bold leading-none transition-colors"
              aria-label="About this chart"
            >
              ?
            </button>
            <div className="invisible group-hover:visible absolute left-0 top-full mt-1.5 w-72 rounded-lg bg-gray-900 text-white text-xs px-3 py-2.5 leading-relaxed shadow-xl z-50 pointer-events-none">
              <div className="absolute -top-1 left-1.5 w-2 h-2 bg-gray-900 rotate-45" />
              {description}
            </div>
          </div>
        )}
        {onExport && (
          <button
            type="button"
            onClick={() => { setShowExportMenu(false); onExport() }}
            className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
            aria-label="Export chart data as CSV"
            title="Export chart data as CSV"
          >
            <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
        )}
      </div>
      {children}
    </div>
  )
}
