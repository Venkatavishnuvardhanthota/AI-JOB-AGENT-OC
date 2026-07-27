import { Sidebar } from './sidebar'
import { Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-dark-950 text-foreground">
      <Sidebar />
      <main className="flex-1 p-4 md:p-6 md:ml-60 pb-16 md:pb-6">
        <Outlet />
      </main>
    </div>
  )
}
