import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import EligibilityFunnel from '../EligibilityFunnel'

const data = {
  total: 1000,
  eligible: 250,
  eligible_pct: 25.0,
  steps: [
    { key: 'all', label: 'All patients', count: 1000 },
    { key: 'disease_stage', label: 'Disease & stage', count: 500 },
    { key: 'geography', label: 'Geography', count: 250 },
  ],
}

describe('EligibilityFunnel', () => {
  it('renders headline eligible count and share of population', () => {
    render(<EligibilityFunnel data={data} />)
    expect(screen.getByText('250')).toBeInTheDocument()
    expect(screen.getByText('eligible (25.0% of 1,000 patients)')).toBeInTheDocument()
  })

  it('renders every funnel step with count and pct of total', () => {
    render(<EligibilityFunnel data={data} />)
    expect(screen.getByText('All patients')).toBeInTheDocument()
    expect(screen.getByText('Disease & stage')).toBeInTheDocument()
    expect(screen.getByText('Geography')).toBeInTheDocument()
    expect(screen.getByText('1,000 · 100.0%')).toBeInTheDocument()
    expect(screen.getByText('500 · 50.0%')).toBeInTheDocument()
    expect(screen.getByText('250 · 25.0%')).toBeInTheDocument()
  })

  it('shows guidance when no filters are applied', () => {
    render(
      <EligibilityFunnel
        data={{
          total: 1000,
          eligible: 1000,
          eligible_pct: 100,
          steps: [{ key: 'all', label: 'All patients', count: 1000 }],
        }}
      />
    )
    expect(screen.getByText(/No cohort filters applied/)).toBeInTheDocument()
  })

  it('shows empty state when total is zero', () => {
    render(<EligibilityFunnel data={{ total: 0, eligible: 0, eligible_pct: 0, steps: [] }} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
