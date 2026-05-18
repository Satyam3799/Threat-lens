const threats = [
  { name: 'CVE-2026-18422 active exploitation', tag: 'Exploit', source: 'CISA KEV mirror', confidence: 'High' },
  { name: 'New credential stuffing cluster', tag: 'Identity', source: 'Internal detections', confidence: 'Medium' },
  { name: 'Ransomware loader infrastructure shift', tag: 'Malware', source: 'Threat intel partner', confidence: 'High' },
  { name: 'Suspicious ASN scanning finance apps', tag: 'Recon', source: 'Honeypot mesh', confidence: 'Medium' },
]

function ThreatFeed() {
  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_22rem]">
      <section className="glass-panel rounded-lg p-5">
        <h2 className="text-xl font-semibold text-white">Threat Feed</h2>
        <p className="mt-1 text-sm text-slate-400">Curated intelligence items for enrichment and analyst review.</p>

        <div className="mt-6 space-y-4">
          {threats.map((threat) => (
            <article key={threat.name} className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <span className="rounded bg-cyan-400/10 px-2.5 py-1 text-xs font-semibold text-cyan-200">{threat.tag}</span>
                  <h3 className="mt-3 text-lg font-semibold text-white">{threat.name}</h3>
                  <p className="mt-1 text-sm text-slate-400">{threat.source}</p>
                </div>
                <span className="rounded-md border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-sm text-emerald-200">
                  {threat.confidence}
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <aside className="glass-panel rounded-lg p-5">
        <h2 className="text-lg font-semibold text-white">Source Health</h2>
        <div className="mt-5 space-y-4">
          {['OSINT', 'EDR', 'NDR', 'Cloud SIEM'].map((source) => (
            <div key={source} className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950/50 p-3">
              <span className="text-sm text-slate-300">{source}</span>
              <span className="flex items-center gap-2 text-sm text-emerald-300">
                <span className="status-dot bg-emerald-300 text-emerald-300" />
                Online
              </span>
            </div>
          ))}
        </div>
      </aside>
    </div>
  )
}

export default ThreatFeed
