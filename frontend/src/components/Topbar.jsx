import { Link, NavLink, useNavigate } from 'react-router-dom'
import { clearAuthToken, isAuthenticated } from '../utils/auth'

const mobileItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Scanner', path: '/scanner' },
  { label: 'Reports', path: '/reports' },
  { label: 'Feed', path: '/threat-feed' },
]

function Topbar() {
  const navigate = useNavigate()
  const isSignedIn = isAuthenticated()

  const handleLogout = () => {
    clearAuthToken()
    navigate('/login', { replace: true })
  }

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl">
      <div className="flex min-h-20 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div>
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">Security Operations</p>
          <h1 className="mt-1 text-xl font-semibold text-white sm:text-2xl">Threat Lens Command Center</h1>
        </div>
        <div className="hidden items-center gap-3 sm:flex">
          <div className="rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-300">
            <span className="text-slate-500">Region</span> IN-SOC-01
          </div>
          {isSignedIn ? (
            <button className="rounded-md bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-100 transition hover:bg-slate-700" onClick={handleLogout}>
              Sign out
            </button>
          ) : (
            <Link className="rounded-md bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300" to="/login">
              Sign in
            </Link>
          )}
        </div>
      </div>

      <nav className="flex gap-2 overflow-x-auto px-4 pb-4 sm:px-6 lg:hidden">
        {mobileItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              [
                'shrink-0 rounded-md px-3 py-2 text-sm font-medium',
                isActive ? 'bg-cyan-400 text-slate-950' : 'bg-slate-900 text-slate-300',
              ].join(' ')
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

export default Topbar
