const bars = [42, 68, 53, 80, 61, 92, 75, 56, 84, 70, 96, 88]

function DummyChart({ title, subtitle }) {
  return (
    <section className="glass-panel rounded-lg p-5">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <p className="mt-1 text-sm text-slate-400">{subtitle}</p>
        </div>
        <span className="rounded-md border border-slate-700 px-2.5 py-1 text-xs text-slate-400">24h</span>
      </div>
      <div className="flex h-48 items-end gap-2 rounded-md border border-slate-800 bg-slate-950/60 p-4">
        {bars.map((height, index) => (
          <div key={index} className="flex flex-1 items-end">
            <div
              className="w-full rounded-t bg-gradient-to-t from-cyan-500 to-emerald-300 opacity-90"
              style={{ height: `${height}%` }}
              aria-label={`Signal volume ${height}`}
            />
          </div>
        ))}
      </div>
    </section>
  )
}

export default DummyChart
