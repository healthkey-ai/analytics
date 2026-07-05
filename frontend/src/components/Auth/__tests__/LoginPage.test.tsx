import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import LoginPage from '../LoginPage'
import type { AuthState } from '../../../hooks/useAuth'

function makeAuth(overrides?: Partial<AuthState>): AuthState {
  return {
    user: null,
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    signup: vi.fn(),
    ...overrides,
  }
}

describe('LoginPage', () => {
  beforeEach(() => vi.clearAllMocks())

  describe('initial render (Sign In mode)', () => {
    it('renders the Sign In tab button', () => {
      render(<LoginPage auth={makeAuth()} />)
      // Both the tab and the submit button are named "Sign In" in login mode
      const signInBtns = screen.getAllByRole('button', { name: 'Sign In' })
      expect(signInBtns.length).toBeGreaterThanOrEqual(1)
    })

    it('does not show the Name field in Sign In mode', () => {
      render(<LoginPage auth={makeAuth()} />)
      expect(screen.queryByPlaceholderText('Your name')).not.toBeInTheDocument()
    })

    it('shows a single password input in Sign In mode', () => {
      render(<LoginPage auth={makeAuth()} />)
      // Only one password input should exist (the Confirm Password field is hidden)
      expect(screen.getAllByPlaceholderText('••••••••')).toHaveLength(1)
    })

    it('shows email and password inputs', () => {
      render(<LoginPage auth={makeAuth()} />)
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument()
    })
  })

  describe('switching to Sign Up tab', () => {
    it('shows the Name field after switching to Sign Up', async () => {
      render(<LoginPage auth={makeAuth()} />)
      await userEvent.click(screen.getByRole('button', { name: 'Sign Up' }))
      expect(screen.getByPlaceholderText('Your name')).toBeInTheDocument()
    })

    it('shows two password inputs (Password + Confirm Password) after switching to Sign Up', async () => {
      render(<LoginPage auth={makeAuth()} />)
      await userEvent.click(screen.getByRole('button', { name: 'Sign Up' }))
      expect(screen.getAllByPlaceholderText('••••••••')).toHaveLength(2)
    })

    it('shows the Create Account submit button in Sign Up mode', async () => {
      render(<LoginPage auth={makeAuth()} />)
      await userEvent.click(screen.getByRole('button', { name: 'Sign Up' }))
      expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument()
    })
  })

  describe('password mismatch validation on signup', () => {
    it('shows an error message when passwords do not match', async () => {
      render(<LoginPage auth={makeAuth()} />)
      await userEvent.click(screen.getByRole('button', { name: 'Sign Up' }))

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'user@example.com')

      // In signup mode there are two password inputs in DOM order: [0]=Password, [1]=Confirm Password
      const [passwordInput, confirmInput] = screen.getAllByPlaceholderText('••••••••')
      await userEvent.type(passwordInput, 'secret123')
      await userEvent.type(confirmInput, 'different!')

      await userEvent.click(screen.getByRole('button', { name: 'Create Account' }))

      expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument()
    })

    it('does not call auth.signup when passwords do not match', async () => {
      const signup = vi.fn()
      render(<LoginPage auth={makeAuth({ signup })} />)
      await userEvent.click(screen.getByRole('button', { name: 'Sign Up' }))

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'user@example.com')
      const [passwordInput, confirmInput] = screen.getAllByPlaceholderText('••••••••')
      await userEvent.type(passwordInput, 'abc')
      await userEvent.type(confirmInput, 'xyz')

      await userEvent.click(screen.getByRole('button', { name: 'Create Account' }))

      expect(signup).not.toHaveBeenCalled()
    })
  })

  describe('submitting state', () => {
    it('shows "Please wait…" on the submit button while the login request is in flight', async () => {
      // login returns a promise that never resolves so we stay in the submitting state
      const login = vi.fn(() => new Promise<void>(() => {}))
      render(<LoginPage auth={makeAuth({ login })} />)

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'user@example.com')
      await userEvent.type(screen.getByPlaceholderText('••••••••'), 'password123')

      // Two "Sign In" buttons in login mode (tab + submit); click the submit (last)
      await userEvent.click(screen.getAllByRole('button', { name: 'Sign In' }).at(-1)!)

      expect(await screen.findByText('Please wait…')).toBeInTheDocument()
    })

    it('disables the submit button while submitting', async () => {
      const login = vi.fn(() => new Promise<void>(() => {}))
      render(<LoginPage auth={makeAuth({ login })} />)

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'user@example.com')
      await userEvent.type(screen.getByPlaceholderText('••••••••'), 'password123')

      // Two "Sign In" buttons in login mode (tab + submit); click the submit (last)
      await userEvent.click(screen.getAllByRole('button', { name: 'Sign In' }).at(-1)!)

      const submitBtn = await screen.findByRole('button', { name: 'Please wait…' })
      expect(submitBtn).toBeDisabled()
    })
  })

  describe('API error handling', () => {
    it('shows a server error message when login rejects with a detail field', async () => {
      const login = vi.fn().mockRejectedValue({
        response: { data: { detail: 'Invalid credentials.' } },
      })
      render(<LoginPage auth={makeAuth({ login })} />)

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'bad@example.com')
      await userEvent.type(screen.getByPlaceholderText('••••••••'), 'wrongpass')
      // Two "Sign In" buttons in login mode (tab + submit); click the submit (last)
      await userEvent.click(screen.getAllByRole('button', { name: 'Sign In' }).at(-1)!)

      expect(await screen.findByText('Invalid credentials.')).toBeInTheDocument()
    })

    it('shows a fallback error message when login rejects without a detail field', async () => {
      const login = vi.fn().mockRejectedValue(new Error('Network Error'))
      render(<LoginPage auth={makeAuth({ login })} />)

      await userEvent.type(screen.getByPlaceholderText('you@example.com'), 'bad@example.com')
      await userEvent.type(screen.getByPlaceholderText('••••••••'), 'wrongpass')
      // Two "Sign In" buttons in login mode (tab + submit); click the submit (last)
      await userEvent.click(screen.getAllByRole('button', { name: 'Sign In' }).at(-1)!)

      expect(await screen.findByText('Something went wrong. Please try again.')).toBeInTheDocument()
    })
  })
})
