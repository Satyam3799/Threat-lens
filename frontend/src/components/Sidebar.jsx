import { NavLink } from 'react-router-dom'
import { API_BASE_URL } from '../services/api'

const navItems = [
  { label: 'Dashboard', path: '/', icon: 'grid' },
  { label: 'Vulnerability Scanner', path: '/scanner', icon: 'scan' },
  { label: 'Scan Reports', path: '/reports', icon: 'report' },
  { label: 'Threat Feed', path: '/threat-feed', icon: 'feed' },
]

function NavIcon({ type }) {
  const common = 'h-5 w-5'

  if (type === 'scan') {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 7V4h3M17 4h3v3M20 17v3h-3M7 20H4v-3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M8 12h8M12 8v8" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    )
  }

  if (type === 'report') {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M7 3h7l4 4v14H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Z" stroke="currentColor" strokeWidth="1.8" />
        <path d="M14 3v5h5M8 14h8M8 18h5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    )
  }

  if (type === 'feed') {
    return (
      <svg className={common} viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M5 18.5c4-7 8-7 14-13M6 6h4v4H6zM14 14h4v4h-4z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    )
  }

  return (
    <svg className={common} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M4 5a1 1 0 0 1 1-1h5v7H4V5ZM14 4h5a1 1 0 0 1 1 1v4h-6V4ZM4 15h6v5H5a1 1 0 0 1-1-1v-4ZM14 13h6v6a1 1 0 0 1-1 1h-5v-7Z" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  )
}

function Sidebar() {
  return (
    <aside className="glass-panel fixed inset-y-0 left-0 z-30 hidden w-72 flex-col rounded-r-lg border-l-0 lg:flex">
      <div className="flex h-20 items-center gap-3 border-b border-slate-800/80 px-6">
        <div className="grid h-11 w-11 place-items-center rounded-md border border-cyan-400/30 bg-cyan-400/10 text-cyan-300">
          TL
        </div>
        <div>
          <p className="text-lg font-semibold text-white">Threat Lens</p>
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">SOC Console</p>
        </div>
      </div>

      <nav className="flex-1 space-y-2 px-4 py-6">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              [
                'flex items-center gap-3 rounded-md px-4 py-3 text-sm font-medium transition',
                isActive
                  ? 'bg-cyan-400/12 text-cyan-200 ring-1 ring-cyan-400/20'
                  : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100',
              ].join(' ')
            }
          >
            <NavIcon type={item.icon} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="m-4 rounded-md border border-emerald-400/20 bg-emerald-400/8 p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-emerald-200">
          <span className="status-dot bg-emerald-300 text-emerald-300" />
          Backend Ready
        </div>
        <p className="text-xs leading-5 text-slate-400">API base: {API_BASE_URL}</p>
      </div>
    </aside>
  )
}

export default Sidebar
