import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import TransformationChart from '../TransformationChart'

const data = {
  evaluable: 100,
  unknown: 15,
  transformed_count: 12,
  transformed_pct: 12.0,
  time_to_transformation: {
    n: 10,
    median_months: 28.5,
    histogram: [
      { label: '0–12', count: 2, lo: 0, hi: 12 },
      { label: '12–24', count: 3, lo: 12, hi: 24 },
      { label: '24–36', count: 3, lo: 24, hi: 36 },
      { label: '36–60', count: 1, lo: 36, hi: 60 },
      { label: '60+', count: 1, lo: 60, hi: null },
    ],
  },
  outcome_distribution: [
    { outcome: 'Complete Response', count: 4, pct: 33.3 },
    { outcome: 'Progressive Disease', count: 5, pct: 41.7 },
    { outcome: 'Deceased', count: 3, pct: 25.0 },
  ],
  os_post_transformation: {
    curve: [{ time: 0, survival: 1, at_risk: 12 }],
    n: 12,
    median: 22.4,
  },
}

describe('TransformationChart', () => {
  it('renders transformation count and pct', () => {
    render(<TransformationChart data={data} />)
    expect(screen.getByText('Transformed to DLBCL')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('12.0% of 100 evaluable')).toBeInTheDocument()
  })

  it('renders median time to transformation', () => {
    render(<TransformationChart data={data} />)
    expect(screen.getByText('28.5 mo')).toBeInTheDocument()
  })

  it('renders undocumented count', () => {
    render(<TransformationChart data={data} />)
    expect(screen.getByText('Not documented')).toBeInTheDocument()
    expect(screen.getByText('15')).toBeInTheDocument()
  })

  it('shows the soft-call caveat', () => {
    render(<TransformationChart data={data} />)
    expect(screen.getByText(/Not every patient is biopsied/)).toBeInTheDocument()
  })

  it('renders post-transformation OS legend', () => {
    render(<TransformationChart data={data} />)
    expect(screen.getByText('Post-transformation OS')).toBeInTheDocument()
    expect(screen.getByText(/median 22.4 mo/)).toBeInTheDocument()
  })

  it('shows empty state when nothing is evaluable', () => {
    render(
      <TransformationChart
        data={{ ...data, evaluable: 0, transformed_count: 0, transformed_pct: 0 }}
      />
    )
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
