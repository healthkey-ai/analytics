interface Props {
  title: string
  children: React.ReactNode
  className?: string
  description?: string
}

export default function MetricCard({ title, children, className = '', description }: Props) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm p-5 ${className}`}>
      <div className="flex items-center gap-1.5 mb-4">
        <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide">{title}</h3>
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
      </div>
      {children}
    </div>
  )
}
