import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DiseaseStateSnapshot from '../DiseaseStateSnapshot'

const data = {
  states: [
    { key: 'newly_diagnosed', label: 'Newly Diagnosed', count: 12, pct: 6.0 },
    { key: 'watch_and_wait', label: 'Watch & Wait', count: 30, pct: 15.0 },
    { key: 'in_remission', label: 'In Remission', count: 88, pct: 44.0 },
    { key: 'relapsed_refractory', label: 'Relapsed / Refractory', count: 60, pct: 30.0 },
    { key: 'other', label: 'Other / Unknown', count: 10, pct: 5.0 },
  ],
  total: 200,
}

describe('DiseaseStateSnapshot', () => {
  it('renders every state tile with count and pct', () => {
    render(<DiseaseStateSnapshot data={data} />)
    for (const s of data.states) {
      expect(screen.getByText(s.label)).toBeInTheDocument()
      expect(screen.getByText(s.count.toLocaleString())).toBeInTheDocument()
      expect(screen.getByText(`${s.pct.toFixed(1)}% of cohort`)).toBeInTheDocument()
    }
  })

  it('shows empty state when total is zero', () => {
    render(<DiseaseStateSnapshot data={{ states: [], total: 0 }} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
