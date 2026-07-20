import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect } from 'vitest'
import TherapyCategories from '../TherapyCategories'

const data = {
  first_line: [
    { category: 'Chemotherapy-containing', count: 80, pct: 40.0 },
    { category: 'Monoclonal antibody', count: 75, pct: 37.5 },
  ],
  second_line: [
    { category: 'Bispecific antibody', count: 12, pct: 6.0 },
  ],
  later_line: [],
}

describe('TherapyCategories', () => {
  it('renders line tabs', () => {
    render(<TherapyCategories data={data} />)
    expect(screen.getByText('1st Line')).toBeInTheDocument()
    expect(screen.getByText('2nd Line')).toBeInTheDocument()
    expect(screen.getByText('3rd Line+')).toBeInTheDocument()
  })

  it('shows multi-membership caveat', () => {
    render(<TherapyCategories data={data} />)
    expect(screen.getByText(/more than one category/)).toBeInTheDocument()
  })

  it('shows empty state when the selected line has no data', async () => {
    const user = userEvent.setup()
    render(<TherapyCategories data={data} />)
    await user.click(screen.getByText('3rd Line+'))
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })

  it('shows empty state when data is null', () => {
    // @ts-expect-error — defensive against missing API field
    render(<TherapyCategories data={null} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
