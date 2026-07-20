import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Pod24 from '../Pod24'

const emptyLine = { curve: [], n: 0, median: null }

const data = {
  clock_start: 'first_line_start_date',
  window_months: 24,
  landmark_months: 24,
  groups: [
    { key: 'pod24', label: 'POD24', count: 30, pct: 50.0 },
    { key: 'no_pod24', label: 'No POD24', count: 20, pct: 33.3 },
    { key: 'unevaluable', label: 'Unevaluable (< 24 months follow-up)', count: 10, pct: 16.7 },
  ],
  os: [
    { label: 'POD24', curve: [{ time: 0, survival: 1, at_risk: 30 }], n: 30, median: 40.5 },
    { label: 'No POD24', curve: [{ time: 0, survival: 1, at_risk: 20 }], n: 20, median: null },
  ],
  os_p: 0.032,
}

describe('Pod24', () => {
  it('renders group counts and pcts', () => {
    render(<Pod24 data={data} />)
    // "POD24" appears in both the count tile and the KM legend
    expect(screen.getAllByText('POD24').length).toBeGreaterThan(0)
    expect(screen.getByText('30')).toBeInTheDocument()
    expect(screen.getByText('50.0% of cohort')).toBeInTheDocument()
    expect(screen.getAllByText('No POD24').length).toBeGreaterThan(0)
    expect(screen.getByText('20')).toBeInTheDocument()
  })

  it('renders unevaluable group', () => {
    render(<Pod24 data={data} />)
    expect(screen.getByText(/Unevaluable/)).toBeInTheDocument()
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('renders p-value badge', () => {
    render(<Pod24 data={data} />)
    expect(screen.getByText('p = 0.032')).toBeInTheDocument()
  })

  it('states where the clock starts and that OS is landmarked', () => {
    render(<Pod24 data={data} />)
    expect(screen.getByText(/Clock starts at/)).toBeInTheDocument()
    expect(screen.getByText(/24-month landmark/)).toBeInTheDocument()
  })

  it('omits p-value badge when p is null', () => {
    render(<Pod24 data={{ ...data, os_p: null }} />)
    expect(screen.queryByText(/^p =/)).not.toBeInTheDocument()
  })

  it('shows empty state when data is null', () => {
    // @ts-expect-error — defensive against missing API field
    render(<Pod24 data={null} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('drops KM lines with empty curves instead of drawing a phantom 100% line', () => {
    render(
      <Pod24
        data={{
          ...data,
          os: [data.os[0], { ...emptyLine, label: 'No POD24', n: 0, median: null }],
        }}
      />
    )
    // The empty arm must not appear in the chart legend — but its count tile stays
    expect(screen.queryByText(/median NR/)).not.toBeInTheDocument()
    expect(screen.getByText('20')).toBeInTheDocument()
  })
})
