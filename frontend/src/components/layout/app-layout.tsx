import { Sidebar } from './sidebar'
import { Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-dark-950 text-foreground">
      <Sidebar />
      <main className="ml-60 flex-1 p-6">
        <Outlet />
      </main>
    </div>
  )
}
