import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import SaveCohortModal from '../SaveCohortModal'
import * as client from '../../../api/client'
import type { CohortFilters, SavedCohort } from '../../../types'

vi.mock('../../../api/client', () => ({
  createSavedCohort: vi.fn(),
  updateSavedCohort: vi.fn(),
}))

const mockFilters: CohortFilters = { disease: 'Multiple Myeloma' }

const mockCohort: SavedCohort = {
  id: 1,
  name: 'Test Cohort',
  description: '',
  filters: mockFilters,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('SaveCohortModal', () => {
  const onSaved = vi.fn()
  const onClose = vi.fn()

  beforeEach(() => vi.clearAllMocks())

  describe('without active cohort', () => {
    it('renders the name input and Save as new button', () => {
      render(<SaveCohortModal filters={mockFilters} onSaved={onSaved} onClose={onClose} />)
      expect(screen.getByText('Save Cohort')).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/e\.g\. High-risk MM/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Save as new' })).toBeInTheDocument()
    })

    it('does not show an Update button', () => {
      render(<SaveCohortModal filters={mockFilters} onSaved={onSaved} onClose={onClose} />)
      expect(screen.queryByText(/Update/)).not.toBeInTheDocument()
    })

    it('shows error when submitting without a name', async () => {
      render(<SaveCohortModal filters={mockFilters} onSaved={onSaved} onClose={onClose} />)
      await userEvent.click(screen.getByRole('button', { name: 'Save as new' }))
      expect(await screen.findByText('Name is required.')).toBeInTheDocument()
      expect(client.createSavedCohort).not.toHaveBeenCalled()
    })

    it('calls createSavedCohort with trimmed name and current filters', async () => {
      vi.mocked(client.createSavedCohort).mockResolvedValue(mockCohort)
      render(<SaveCohortModal filters={mockFilters} onSaved={onSaved} onClose={onClose} />)
      await userEvent.type(screen.getByPlaceholderText(/e\.g\. High-risk MM/), 'My Cohort')
      await userEvent.click(screen.getByRole('button', { name: 'Save as new' }))
      await waitFor(() => {
        expect(client.createSavedCohort).toHaveBeenCalledWith({
          name: 'My Cohort',
          description: '',
          filters: mockFilters,
        })
        expect(onSaved).toHaveBeenCalledWith(mockCohort)
      })
    })

    it('calls onClose when Cancel is clicked', async () => {
      render(<SaveCohortModal filters={mockFilters} onSaved={onSaved} onClose={onClose} />)
      await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('with active cohort', () => {
    const activeProps = {
      filters: mockFilters,
      activeCohortId: 1,
      activeCohortName: 'My Cohort',
      onSaved,
      onClose,
    }

    it('shows Update button with cohort name', () => {
      render(<SaveCohortModal {...activeProps} />)
      expect(screen.getByRole('button', { name: 'Update "My Cohort"' })).toBeInTheDocument()
    })

    it('shows the "or save as new" divider', () => {
      render(<SaveCohortModal {...activeProps} />)
      expect(screen.getByText('or save as new')).toBeInTheDocument()
    })

    it('pre-fills the name input with the active cohort name', () => {
      render(<SaveCohortModal {...activeProps} />)
      const input = screen.getByPlaceholderText(/e\.g\. High-risk MM/) as HTMLInputElement
      expect(input.value).toBe('My Cohort')
    })

    it('calls updateSavedCohort with current filters when Update is clicked', async () => {
      vi.mocked(client.updateSavedCohort).mockResolvedValue({ ...mockCohort, name: 'My Cohort' })
      render(<SaveCohortModal {...activeProps} />)
      await userEvent.click(screen.getByRole('button', { name: 'Update "My Cohort"' }))
      await waitFor(() => {
        expect(client.updateSavedCohort).toHaveBeenCalledWith(1, { filters: mockFilters })
        expect(onSaved).toHaveBeenCalled()
      })
    })

    it('still allows saving as new when name is entered', async () => {
      vi.mocked(client.createSavedCohort).mockResolvedValue({ ...mockCohort, id: 2, name: 'Copy' })
      render(<SaveCohortModal {...activeProps} />)
      const input = screen.getByPlaceholderText(/e\.g\. High-risk MM/)
      await userEvent.clear(input)
      await userEvent.type(input, 'Copy')
      await userEvent.click(screen.getByRole('button', { name: 'Save as new' }))
      await waitFor(() => {
        expect(client.createSavedCohort).toHaveBeenCalledWith(
          expect.objectContaining({ name: 'Copy' })
        )
      })
    })
  })
})
