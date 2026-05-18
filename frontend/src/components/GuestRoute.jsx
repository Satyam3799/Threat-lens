import { Navigate, Outlet } from 'react-router-dom'
import { isAuthenticated } from '../utils/auth'

function GuestRoute() {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

export default GuestRoute
