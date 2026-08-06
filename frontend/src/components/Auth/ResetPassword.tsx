import { useState } from 'react'
import { resetPassword } from '../../api/client'

type State = 'ready' | 'success' | 'error'

export default function ResetPassword({ uid, token }: { uid: string; token: string }) {
  const [state, setState] = useState<State>('ready')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirm) {
      setMessage('Passwords do not match.')
      return
    }
    setMessage('')
    setSubmitting(true)
    try {
      await resetPassword(uid, token, password)
      setState('success')
      setMessage('Password has been reset. You can now sign in.')
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setMessage(detail ?? 'Could not reset your password. The link may have expired.')
      setState('error')
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
          <div>
            <h2 className="text-white font-semibold text-sm">Choose a new password</h2>
          </div>

          {state === 'ready' && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs text-slate-400 mb-1">New password</label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  autoComplete="new-password"
                  placeholder="At least 12 characters"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
              <div>
                <label className="block text-xs text-slate-400 mb-1">Confirm password</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  required
                  autoComplete="new-password"
                  placeholder="••••••••"
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
                />
              </div>
              {message && (
                <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
                  {message}
                </p>
              )}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
              >
                {submitting ? 'Please wait…' : 'Reset password'}
              </button>
            </form>
          )}

          {state === 'success' && (
            <div className="space-y-4">
              <p className="text-xs text-teal-400 bg-teal-900/20 border border-teal-800 rounded-lg px-3 py-2">
                {message}
              </p>
              <button
                onClick={() => window.location.replace('/')}
                className="w-full bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors"
              >
                Go to sign in
              </button>
            </div>
          )}

          {state === 'error' && (
            <div className="space-y-4">
              <p className="text-xs text-red-400 bg-red-900/20 border border-red-800 rounded-lg px-3 py-2">
                {message}
              </p>
              <button
                onClick={() => window.location.replace('/')}
                className="w-full border border-slate-600 text-slate-300 hover:text-white rounded-lg py-2.5 text-sm transition-colors"
              >
                Back to sign in
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
