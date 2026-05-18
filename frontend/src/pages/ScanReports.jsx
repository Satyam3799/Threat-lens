import { useScanHistory } from '../hooks/useScanHistory'

function ScanReports() {
  const { history, loading, error, refresh } = useScanHistory(50)

  return (
    <section className="glass-panel overflow-hidden rounded-lg">
      <div className="flex flex-col gap-4 border-b border-slate-800 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Scan History</h2>
          <p className="mt-1 text-sm text-slate-400">PostgreSQL-backed record of Nmap scan results.</p>
        </div>
        <button onClick={refresh} className="rounded-md border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-cyan-400 hover:text-cyan-200">
          Refresh
        </button>
      </div>

      {error && <p className="m-5 rounded-md border border-rose-400/20 bg-rose-400/10 p-3 text-sm text-rose-200">{error}</p>}

      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.16em] text-slate-500">
            <tr>
              <th className="px-5 py-4 font-semibold">Scan ID</th>
              <th className="px-5 py-4 font-semibold">Target</th>
              <th className="px-5 py-4 font-semibold">Open Ports</th>
              <th className="px-5 py-4 font-semibold">Status</th>
              <th className="px-5 py-4 font-semibold">Scanner</th>
              <th className="px-5 py-4 font-semibold">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {history.map((report) => (
              <tr key={report.id} className="bg-slate-900/35 transition hover:bg-slate-900/70">
                <td className="px-5 py-4 font-medium text-cyan-200">#{report.id}</td>
                <td className="px-5 py-4 break-all text-slate-200">{report.target}</td>
                <td className="px-5 py-4 text-white">{report.open_ports_count}</td>
                <td className="px-5 py-4">
                  <span className="rounded bg-slate-800 px-2.5 py-1 text-slate-200">{report.status}</span>
                </td>
                <td className="px-5 py-4 text-slate-400">{report.scanner}</td>
                <td className="px-5 py-4 text-slate-400">{new Date(report.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {!loading && history.length === 0 && (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan="6">No scans have been stored yet.</td>
              </tr>
            )}
            {loading && (
              <tr>
                <td className="px-5 py-8 text-center text-slate-400" colSpan="6">Loading scan history...</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ScanReports
