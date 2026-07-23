import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Briefcase,
  FileText,
  UserCircle,
  Activity,
  Settings,
  BarChart3,
  ChevronLeft,
  Menu,
  LogOut,
  Cpu,
  FileSpreadsheet,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'

interface NavItem {
  label: string
  icon: React.ElementType
  href: string
  children?: { label: string; href: string }[]
}

const navItems: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
  {
    label: 'Jobs', icon: Briefcase, href: '/jobs',
    children: [
      { label: 'Search', href: '/jobs/search' },
      { label: 'Saved', href: '/jobs/saved' },
    ],
  },
  { label: 'Applications', icon: FileText, href: '/applications' },
  { label: 'Resume Library', icon: FileSpreadsheet, href: '/resumes' },
  { label: 'Career Profile', icon: UserCircle, href: '/profile' },
  {
    label: 'Workflows', icon: Activity, href: '/workflows',
    children: [
      { label: 'Monitor', href: '/workflows/monitor' },
      { label: 'Orchestrations', href: '/workflows/orchestrations' },
      { label: 'History', href: '/workflows/history' },
    ],
  },
  {
    label: 'Infrastructure', icon: Cpu, href: '/infrastructure',
    children: [
      { label: 'Operations', href: '/infrastructure/operations' },
      { label: 'Browser Sessions', href: '/infrastructure/browser-sessions' },
      { label: 'Providers', href: '/infrastructure/providers' },
      { label: 'Logs', href: '/infrastructure/logs' },
    ],
  },
  { label: 'Reports', icon: BarChart3, href: '/reports' },
  {
    label: 'Settings', icon: Settings, href: '/settings',
    children: [
      { label: 'Account', href: '/settings/account' },
      { label: 'Preferences', href: '/settings/preferences' },
    ],
  },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(['Jobs', 'Workflows', 'Infrastructure', 'Settings']))
  const location = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const toggleExpand = (label: string) => {
    setExpandedItems(prev => {
      const next = new Set(prev)
      if (next.has(label)) next.delete(label)
      else next.add(label)
      return next
    })
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const isActive = (href: string) => location.pathname === href || location.pathname.startsWith(href + '/')

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-glass-border bg-dark-900 transition-all duration-300",
        collapsed ? "w-16" : "w-60"
      )}
    >
      <div className={cn("flex h-14 items-center border-b border-glass-border px-4", collapsed && "justify-center")}>
        {!collapsed && (
          <Link to="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-secondary text-white text-xs font-bold">
              AJ
            </div>
            <span className="font-semibold text-foreground text-sm">AI Job Agent</span>
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn("ml-auto", collapsed && "ml-0")}
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2">
        {navItems.map(item => {
          const Icon = item.icon
          const hasChildren = item.children && item.children.length > 0
          const active = isActive(item.href)
          const expanded = expandedItems.has(item.label)

          return (
            <div key={item.label}>
              {hasChildren ? (
                <>
                  <button
                    onClick={() => toggleExpand(item.label)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                      active && "bg-primary/10 text-primary",
                      collapsed && "justify-center px-2"
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    {!collapsed && (
                      <>
                        <span className="flex-1 text-left">{item.label}</span>
                        <ChevronLeft className={cn("h-3 w-3 transition-transform", expanded && "-rotate-90")} />
                      </>
                    )}
                  </button>
                  {!collapsed && expanded && (
                    <div className="ml-6 mt-1 space-y-1">
                      {item.children!.map(child => (
                        <Link
                          key={child.href}
                          to={child.href}
                          className={cn(
                            "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition-colors hover:bg-white/5",
                            location.pathname === child.href
                              ? "text-primary bg-primary/5"
                              : "text-muted-foreground"
                          )}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <Link
                  to={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                    active ? "bg-primary/10 text-primary" : "text-muted-foreground",
                    collapsed && "justify-center px-2"
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {!collapsed && <span>{item.label}</span>}
                </Link>
              )}
            </div>
          )
        })}
      </nav>

      <div className="border-t border-glass-border p-2">
        {!collapsed && user && (
          <div className="mb-2 px-3 py-2">
            <p className="text-xs text-muted-foreground truncate">{user.email}</p>
          </div>
        )}
        <Button
          variant="ghost"
          size={collapsed ? "icon" : "default"}
          className={cn("w-full", collapsed ? "justify-center" : "justify-start gap-3")}
          onClick={handleLogout}
        >
          <LogOut className="h-4 w-4" />
          {!collapsed && <span>Logout</span>}
        </Button>
      </div>
    </aside>
  )
}
