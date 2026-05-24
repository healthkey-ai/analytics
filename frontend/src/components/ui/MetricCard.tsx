interface Props {
  title: string
  children: React.ReactNode
  className?: string
}

export default function MetricCard({ title, children, className = '' }: Props) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm p-5 ${className}`}>
      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">{title}</h3>
      {children}
    </div>
  )
}
