import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { authApi } from '../services/api'
import { setAuthToken } from '../utils/auth'

function LoginRegister({ mode }) {
  const isRegister = mode === 'register'
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)

  const updateField = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setStatus('')

    try {
      const payload = isRegister
        ? { full_name: form.name, email: form.email, password: form.password }
        : { email: form.email, password: form.password }
      const response = isRegister ? await authApi.register(payload) : await authApi.login(payload)

      if (response.data?.access_token) {
        setAuthToken(response.data.access_token)
        navigate('/', { replace: true })
        return
      }

      if (isRegister) {
        setStatus('Account created. Redirecting to sign in...')
        setTimeout(() => navigate('/login', { replace: true }), 600)
        return
      }

      setStatus('Signed in successfully.')
    } catch (error) {
      setStatus(error.response?.data?.detail || 'Unable to complete request. Check the API server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="glass-panel w-full max-w-md rounded-lg p-6 sm:p-8">
      <div className="mb-8">
        <div className="mb-5 grid h-12 w-12 place-items-center rounded-md border border-cyan-400/30 bg-cyan-400/10 font-semibold text-cyan-200">
          TL
        </div>
        <h1 className="text-2xl font-semibold text-white">{isRegister ? 'Create analyst account' : 'Sign in to Threat Lens'}</h1>
        <p className="mt-2 text-sm text-slate-400">Access the SOC dashboard and scanner workflows.</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        {isRegister && (
          <label className="block">
            <span className="text-sm font-medium text-slate-300">Name</span>
            <input name="name" value={form.name} onChange={updateField} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400" required />
          </label>
        )}
        <label className="block">
          <span className="text-sm font-medium text-slate-300">Email</span>
          <input name="email" type="email" value={form.email} onChange={updateField} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400" required />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-slate-300">Password</span>
          <input name="password" type="password" value={form.password} onChange={updateField} className="mt-2 w-full rounded-md border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition focus:border-cyan-400" required />
        </label>

        {status && <p className="rounded-md border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-300">{status}</p>}

        <button className="w-full rounded-md bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60" disabled={loading}>
          {loading ? 'Processing...' : isRegister ? 'Create account' : 'Sign in'}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-slate-400">
        {isRegister ? 'Already have an account?' : 'Need an account?'}{' '}
        <Link className="font-semibold text-cyan-300 hover:text-cyan-200" to={isRegister ? '/login' : '/register'}>
          {isRegister ? 'Sign in' : 'Register'}
        </Link>
      </p>
    </section>
  )
}

export default LoginRegister
