import { BrowserDashboard } from '@/components/browser/browser-dashboard'
import { BrowserList } from '@/components/browser/browser-list'
import { BrowserMonitor } from '@/components/browser/browser-monitor'
import { SessionList } from '@/components/browser/session-list'
import { PageHeader } from '@/components/layout/page-header'

export function BrowserSessionsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Browser Automation"
        description="Manage browser automation sessions and monitor performance."
      />
      <BrowserDashboard />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <BrowserList />
          <SessionList />
        </div>
        <div className="space-y-6">
          <BrowserMonitor />
        </div>
      </div>
    </div>
  )
}
