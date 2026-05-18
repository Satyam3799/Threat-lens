import { Outlet } from 'react-router-dom'

function AuthLayout() {
  return (
    <main className="grid min-h-screen place-items-center px-4 py-10 text-slate-100">
      <Outlet />
    </main>
  )
}

export default AuthLayout
