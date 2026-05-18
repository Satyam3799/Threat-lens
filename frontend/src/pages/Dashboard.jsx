import DummyChart from '../components/DummyChart'
import StatCard from '../components/StatCard'
import { useScanHistory } from '../hooks/useScanHistory'

const incidents = [
  { asset: 'api-gateway-01', type: 'Brute force spike', severity: 'High', time: '4 min ago' },
  { asset: 'vpn-edge', type: 'Impossible travel', severity: 'Medium', time: '18 min ago' },
  { asset: 'db-cluster-a', type: 'Privilege escalation attempt', severity: 'Critical', time: '31 min ago' },
]

function Dashboard() {
  const { history } = useScanHistory(5)
  const completedScans = history.filter((scan) => scan.status === 'completed').length
  const openPorts = history.reduce((total, scan) => total + scan.open_ports_count, 0)

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Active Threats" value="27" trend="+8 signals in the last hour" tone="rose" />
        <StatCard label="Assets Monitored" value="1,284" trend="99.98% sensor coverage" tone="cyan" />
        <StatCard label="Completed Scans" value={completedScans} trend="Loaded from scan history" tone="emerald" />
        <StatCard label="Open Ports Found" value={openPorts} trend="Across recent Nmap scans" tone="amber" />
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <DummyChart title="Threat Signal Volume" subtitle="Normalized detections across network, identity, endpoint, and cloud sources." />

        <div className="glass-panel rounded-lg p-5">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-white">Priority Incidents</h2>
              <p className="mt-1 text-sm text-slate-400">Triage queue by current impact</p>
            </div>
            <span className="rounded-md bg-rose-400/10 px-3 py-1 text-sm font-semibold text-rose-200">3 live</span>
          </div>
          <div className="space-y-3">
            {incidents.map((incident) => (
              <article key={incident.asset} className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-medium text-white">{incident.type}</p>
                  <span className="text-xs text-slate-500">{incident.time}</span>
                </div>
                <div className="mt-3 flex items-center justify-between gap-3 text-sm">
                  <span className="text-slate-400">{incident.asset}</span>
                  <span className="rounded bg-slate-800 px-2 py-1 text-slate-200">{incident.severity}</span>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="glass-panel rounded-lg p-5">
        <h2 className="text-lg font-semibold text-white">Latest Scan History</h2>
        <div className="mt-4 grid gap-3 lg:grid-cols-5">
          {history.map((scan) => (
            <article key={scan.id} className="rounded-md border border-slate-800 bg-slate-950/55 p-4">
              <p className="break-all text-sm font-medium text-white">{scan.target}</p>
              <p className="mt-2 text-2xl font-semibold text-cyan-200">{scan.open_ports_count}</p>
              <p className="text-xs text-slate-500">open ports</p>
            </article>
          ))}
          {history.length === 0 && <p className="text-sm text-slate-400">No scans have been run yet.</p>}
        </div>
      </section>
    </div>
  )
}

export default Dashboard
