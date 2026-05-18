function StatCard({ label, value, trend, tone = 'cyan' }) {
  const toneClasses = {
    cyan: 'text-cyan-300 bg-cyan-400/10 border-cyan-400/20',
    emerald: 'text-emerald-300 bg-emerald-400/10 border-emerald-400/20',
    amber: 'text-amber-300 bg-amber-400/10 border-amber-400/20',
    rose: 'text-rose-300 bg-rose-400/10 border-rose-400/20',
  }

  return (
    <article className="glass-panel rounded-lg p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="mt-3 text-3xl font-semibold text-white">{value}</p>
        </div>
        <span className={`rounded-md border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}>
          Live
        </span>
      </div>
      <p className="mt-4 text-sm text-slate-400">{trend}</p>
    </article>
  )
}

export default StatCard
