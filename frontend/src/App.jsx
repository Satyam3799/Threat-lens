import { Navigate, Route, Routes } from 'react-router-dom'
import GuestRoute from './components/GuestRoute'
import ProtectedRoute from './components/ProtectedRoute'
import AppLayout from './layouts/AppLayout'
import AuthLayout from './layouts/AuthLayout'
import Dashboard from './pages/Dashboard'
import LoginRegister from './pages/LoginRegister'
import ScanReports from './pages/ScanReports'
import ThreatFeed from './pages/ThreatFeed'
import VulnerabilityScanner from './pages/VulnerabilityScanner'

function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<AuthLayout />}>
          <Route index element={<LoginRegister mode="login" />} />
        </Route>
        <Route path="/register" element={<AuthLayout />}>
          <Route index element={<LoginRegister mode="register" />} />
        </Route>
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="scanner" element={<VulnerabilityScanner />} />
          <Route path="reports" element={<ScanReports />} />
          <Route path="threat-feed" element={<ThreatFeed />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
