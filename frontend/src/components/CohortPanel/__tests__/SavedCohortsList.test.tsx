import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import SavedCohortsList from '../SavedCohortsList'
import * as client from '../../../api/client'
import type { SavedCohort } from '../../../types'

vi.mock('../../../api/client', () => ({
  fetchSavedCohorts: vi.fn(),
  updateSavedCohort: vi.fn(),
  deleteSavedCohort: vi.fn(),
}))

const mockCohorts: SavedCohort[] = [
  {
    id: 1,
    name: 'ISS Stage I',
    description: 'Stage 1 patients',
    filters: { disease: 'Multiple Myeloma', stage: ['ISS Stage I'] },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Triple Refractory',
    description: '',
    filters: { disease: 'Multiple Myeloma' },
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
]

describe('SavedCohortsList', () => {
  const onLoad = vi.fn()

  beforeEach(() => vi.clearAllMocks())

  it('shows loading indicator initially', () => {
    vi.mocked(client.fetchSavedCohorts).mockReturnValue(new Promise(() => {}))
    render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    expect(screen.getByText('Loading…')).toBeInTheDocument()
  })

  it('renders cohort names after successful fetch', async () => {
    vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
    render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    expect(await screen.findByText('ISS Stage I')).toBeInTheDocument()
    expect(screen.getByText('Triple Refractory')).toBeInTheDocument()
  })

  it('shows description when present', async () => {
    vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
    render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    expect(await screen.findByText('Stage 1 patients')).toBeInTheDocument()
  })

  it('shows empty state when no cohorts', async () => {
    vi.mocked(client.fetchSavedCohorts).mockResolvedValue([])
    render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    expect(await screen.findByText('No saved cohorts yet.')).toBeInTheDocument()
  })

  it('shows error message on fetch failure', async () => {
    vi.mocked(client.fetchSavedCohorts).mockRejectedValue(new Error('Network error'))
    render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    expect(await screen.findByText(/Failed to load/)).toBeInTheDocument()
  })

  it('re-fetches when refreshToken changes', async () => {
    vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
    const { rerender } = render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
    await screen.findByText('ISS Stage I')
    rerender(<SavedCohortsList onLoad={onLoad} refreshToken={1} />)
    await waitFor(() => expect(client.fetchSavedCohorts).toHaveBeenCalledTimes(2))
  })

  describe('loading a cohort', () => {
    it('calls onLoad with filters, id, and name when cohort clicked', async () => {
      vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
      render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
      await userEvent.click(await screen.findByText('ISS Stage I'))
      expect(onLoad).toHaveBeenCalledWith(
        mockCohorts[0].filters,
        1,
        'ISS Stage I'
      )
    })
  })

  describe('inline rename', () => {
    it('shows rename input when pencil button clicked', async () => {
      vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
      render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
      await screen.findByText('ISS Stage I')
      await userEvent.click(screen.getAllByTitle('Rename')[0])
      expect(screen.getByDisplayValue('ISS Stage I')).toBeInTheDocument()
    })

    it('calls updateSavedCohort with new name on Enter', async () => {
      vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
      vi.mocked(client.updateSavedCohort).mockResolvedValue({ ...mockCohorts[0], name: 'Renamed' })
      render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
      await screen.findByText('ISS Stage I')
      await userEvent.click(screen.getAllByTitle('Rename')[0])
      const input = screen.getByDisplayValue('ISS Stage I')
      await userEvent.clear(input)
      await userEvent.type(input, 'Renamed{Enter}')
      await waitFor(() => {
        expect(client.updateSavedCohort).toHaveBeenCalledWith(1, { name: 'Renamed' })
      })
    })

    it('cancels rename on Escape without calling API', async () => {
      vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
      render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
      await screen.findByText('ISS Stage I')
      await userEvent.click(screen.getAllByTitle('Rename')[0])
      await userEvent.keyboard('{Escape}')
      await waitFor(() => {
        expect(screen.getByText('ISS Stage I')).toBeInTheDocument()
        expect(client.updateSavedCohort).not.toHaveBeenCalled()
      })
    })

    it('does not call API when name is unchanged', async () => {
      vi.mocked(client.fetchSavedCohorts).mockResolvedValue(mockCohorts)
      render(<SavedCohortsList onLoad={onLoad} refreshToken={0} />)
      await screen.findByText('ISS Stage I')
      await userEvent.click(screen.getAllByTitle('Rename')[0])
      await userEvent.keyboard('{Enter}')
      await waitFor(() => {
        expect(client.updateSavedCohort).not.toHaveBeenCalled()
      })
    })
  })
})
