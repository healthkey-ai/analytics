import { useState } from 'react'
import * as api from '../../api/client'
import type { AuthState } from '../../hooks/useAuth'

interface Props {
  auth: AuthState
}

export default function LoginPage({ auth }: Props) {
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function switchMode(m: 'login' | 'signup' | 'forgot') {
    setMode(m)
    setError('')
    setInfo('')
    setConfirmPassword('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setInfo('')

    if (mode === 'forgot') {
      setSubmitting(true)
      try {
        await api.requestPasswordReset(email)
        setInfo('If an account exists with that email, a reset link has been sent.')
      } catch {
        setError('Something went wrong. Please try again.')
      } finally {
        setSubmitting(false)
      }
      return
    }

    if (mode === 'signup' && password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      if (mode === 'login') {
        await auth.login(email, password)
      } else {
        await auth.signup(email, password, name)
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(detail ?? 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-white">Analytics Platform</h1>
          <p className="text-slate-400 text-sm mt-1">Real-world evidence for oncology research</p>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 space-y-5">
          {mode !== 'forgot' && (
            <div className="flex rounded-lg border border-slate-700 p-0.5 bg-slate-900/50">
              {(['login', 'signup'] as const).map(m => (
                <button
                  key={m}
                  onClick={() => switchMode(m)}
                  className={`flex-1 py-2 text-sm font-semibold rounded-md transition-colors ${
                    mode === m ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  {m === 'login' ? 'Sign In' : 'Sign Up'}
                </button>
              ))}
            </div>
          )}

          {mode === 'forgot' && (
            <div>
              <h2 className="text-white font-semibold text-sm">Reset your password</h2>
              <p className="text-slate-400 text-xs mt-1">Enter your email and we'll send you a reset link.</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'signup' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
            )}

            <div>
              <label className="block text-xs text-slate-400 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
              />
            </div>

            {mode !== 'forgot' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
            )}

            {mode === 'signup' && (
              <div>
                <label className="block text-xs text-slate-400 mb-1">Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
            )}

            {mode === 'signup' && (
              <p className="text-xs text-slate-400 leading-relaxed">
                This platform provides analytics on a set of synthetic data from fictional foundations for demonstration purposes.
                For questions, contact{' '}
                <a href="mailto:support@healthkey.ai" className="text-teal-400 hover:text-teal-300 underline">
                  support@healthkey.ai
                </a>
                .
              </p>
            )}

            {error && (
              <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            {info && (
              <p className="text-xs text-teal-400 bg-teal-900/20 border border-teal-800 rounded-lg px-3 py-2">
                {info}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
            >
              {submitting
                ? 'Please wait…'
                : mode === 'login'
                ? 'Sign In'
                : mode === 'signup'
                ? 'Create Account'
                : 'Send Reset Link'}
            </button>
          </form>

          {mode === 'login' && (
            <p className="text-center text-xs text-slate-500">
              <button
                type="button"
                onClick={() => switchMode('forgot')}
                className="text-teal-400 hover:text-teal-300 underline"
              >
                Forgot password?
              </button>
            </p>
          )}

          {mode === 'forgot' && (
            <p className="text-center text-xs text-slate-500">
              <button
                type="button"
                onClick={() => switchMode('login')}
                className="text-teal-400 hover:text-teal-300 underline"
              >
                Back to sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
