import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import LandmarkResponse from '../LandmarkResponse'

const data = {
  clock_start: 'first_line_start_date',
  landmarks: [
    { months: 12, cr_count: 20, evaluable: 100, pct: 20.0 },
    { months: 24, cr_count: 35, evaluable: 90, pct: 38.9 },
    { months: 30, cr_count: 40, evaluable: 80, pct: 50.0 },
    { months: 36, cr_count: 42, evaluable: 70, pct: 60.0 },
  ],
}

describe('LandmarkResponse', () => {
  it('renders CR counts per landmark', () => {
    render(<LandmarkResponse data={data} />)
    expect(screen.getByText('CR30')).toBeInTheDocument()
    expect(screen.getByText(/40\/80 evaluable/)).toBeInTheDocument()
    expect(screen.getByText(/20\/100 evaluable/)).toBeInTheDocument()
  })

  it('states where the clock starts', () => {
    render(<LandmarkResponse data={data} />)
    expect(screen.getByText(/Clock starts at first-line treatment start/)).toBeInTheDocument()
  })

  it('shows empty state when nothing is evaluable', () => {
    const empty = {
      clock_start: 'first_line_start_date',
      landmarks: [{ months: 30, cr_count: 0, evaluable: 0, pct: 0 }],
    }
    render(<LandmarkResponse data={empty} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
