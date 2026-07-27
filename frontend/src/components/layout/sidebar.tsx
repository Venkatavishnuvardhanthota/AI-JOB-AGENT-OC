import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  UserCircle,
  FileSpreadsheet,
  Briefcase,
  FileText,
  Sparkles,
  Brain,
  BarChart3,
  Bell,
  Settings,
  ChevronLeft,
  Menu,
  LogOut,
  X,
  Calendar,
  Search,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { Badge } from '@/components/ui/badge'
import { Logo } from '@/components/ui/logo'

interface NavItem {
  label: string
  icon: React.ElementType
  href: string
  children?: { label: string; href: string; comingSoon?: boolean }[]
  comingSoon?: boolean
}

const navGroups: { label: string; items: NavItem[] }[] = [
  {
    label: 'Main',
    items: [
      { label: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
      { label: 'Calendar', icon: Calendar, href: '/calendar' },
    ],
  },
  {
    label: 'Career',
    items: [
      { label: 'Profile', icon: UserCircle, href: '/profile' },
      { label: 'Resume Library', icon: FileSpreadsheet, href: '/resumes' },
    ],
  },
  {
    label: 'Jobs',
    items: [
      {
        label: 'Jobs', icon: Briefcase, href: '/jobs',
        children: [
          { label: 'Search', href: '/jobs/search' },
          { label: 'Saved', href: '/jobs/saved' },
          { label: 'Matching', href: '/jobs/search', comingSoon: false },
        ],
      },
      { label: 'Discovery', icon: Search, href: '/discovery' },
    ],
  },
  {
    label: 'AI Tools',
    items: [
      {
        label: 'Applications', icon: FileText, href: '/applications',
        children: [
          { label: 'All Applications', href: '/applications' },
          { label: 'Pipeline Board', href: '/applications/board' },
        ],
      },
      { label: 'Cover Letters', icon: Sparkles, href: '/cover-letters' },
      { label: 'Interview Prep', icon: Brain, href: '#', comingSoon: true },
    ],
  },
  {
    label: 'Operations',
    items: [
      { label: 'Analytics', icon: BarChart3, href: '/analytics' },
      { label: 'Notifications', icon: Bell, href: '#', comingSoon: true },
      { label: 'Settings', icon: Settings, href: '/settings',
        children: [
          { label: 'Account', href: '/settings/account' },
          { label: 'Preferences', href: '/settings/preferences' },
        ],
      },
    ],
  },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set(['Jobs', 'Applications', 'Settings']))
  const location = useLocation()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setCollapsed(true)
      }
    }
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

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

  const isActive = (href: string) => {
    if (href === '#') return false
    return location.pathname === href || location.pathname.startsWith(href + '/')
  }

  const sidebarContent = (
    <>
      <div className={cn("flex h-14 items-center border-b border-glass-border px-4", collapsed && "justify-center")}>
        {!collapsed && (
          <Link to="/dashboard" aria-label="AI Job Agent Home">
            <Logo size="md" />
          </Link>
        )}
        <Button
          variant="ghost"
          size="icon"
          className={cn("ml-auto", collapsed && "ml-0")}
          onClick={() => { if (window.innerWidth < 768) setMobileOpen(false); else setCollapsed(!collapsed) }}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 overflow-y-auto p-2" role="navigation" aria-label="Main navigation">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-3">
            {!collapsed && (
              <p className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                {group.label}
              </p>
            )}
            {group.items.map(item => {
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
                        aria-expanded={expanded}
                        aria-label={item.label}
                      >
                        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                        {!collapsed && (
                          <>
                            <span className="flex-1 text-left">{item.label}</span>
                            <ChevronLeft className={cn("h-3 w-3 transition-transform", expanded && "-rotate-90")} />
                          </>
                        )}
                      </button>
                      {!collapsed && expanded && (
                        <div className="ml-4 mt-1 space-y-0.5" role="list">
                          {item.children!.map(child => (
                            child.comingSoon ? (
                              <div
                                key={child.label}
                                className="flex items-center justify-between rounded-lg px-3 py-1.5 text-xs text-muted-foreground opacity-60"
                              >
                                <span>{child.label}</span>
                                <Badge variant="secondary" className="text-[10px] px-1 py-0">Soon</Badge>
                              </div>
                            ) : (
                              <Link
                                key={child.href}
                                to={child.href}
                                className={cn(
                                  "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition-colors hover:bg-white/5",
                                  location.pathname === child.href
                                    ? "text-primary bg-primary/5"
                                    : "text-muted-foreground"
                                )}
                                aria-label={child.label}
                                role="listitem"
                              >
                                {child.label}
                              </Link>
                            )
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    item.comingSoon ? (
                      <div
                        className={cn(
                          "flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground opacity-60",
                          collapsed && "justify-center px-2"
                        )}
                        title={collapsed ? item.label : undefined}
                      >
                        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                        {!collapsed && (
                          <>
                            <span className="flex-1 text-left">{item.label}</span>
                            <Badge variant="secondary" className="text-[10px] px-1 py-0">Soon</Badge>
                          </>
                        )}
                      </div>
                    ) : (
                      <Link
                        to={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                          active ? "bg-primary/10 text-primary" : "text-muted-foreground",
                          collapsed && "justify-center px-2"
                        )}
                        title={collapsed ? item.label : undefined}
                        aria-label={item.label}
                      >
                        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                        {!collapsed && <span>{item.label}</span>}
                      </Link>
                    )
                  )}
                </div>
              )
            })}
          </div>
        ))}
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
          aria-label="Logout"
        >
          <LogOut className="h-4 w-4" aria-hidden="true" />
          {!collapsed && <span>Logout</span>}
        </Button>
      </div>
    </>
  )

  return (
    <>
      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-glass-border bg-dark-900 transition-all duration-300",
          collapsed ? "w-16" : "w-60",
          "hidden md:flex"
        )}
        role="navigation"
        aria-label="Sidebar navigation"
      >
        {sidebarContent}
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="absolute inset-0 bg-black/50" onClick={() => setMobileOpen(false)} aria-hidden="true" />
          <aside className="relative z-10 flex h-screen w-60 flex-col border-r border-glass-border bg-dark-900">
            <div className="flex h-14 items-center justify-between border-b border-glass-border px-4">
              <Link to="/dashboard" aria-label="AI Job Agent Home">
                <Logo size="md" />
              </Link>
              <Button variant="ghost" size="icon" onClick={() => setMobileOpen(false)} aria-label="Close menu">
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {navGroups.map((group) => (
                <div key={group.label} className="mb-3">
                  <p className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    {group.label}
                  </p>
                  {group.items.map(item => {
                    const Icon = item.icon
                    const hasChildren = item.children && item.children.length > 0
                    const active = isActive(item.href)

                    return (
                      <div key={item.label}>
                        {hasChildren ? (
                          <>
                            <button
                              onClick={() => toggleExpand(item.label)}
                              className={cn(
                                "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                                active && "bg-primary/10 text-primary"
                              )}
                              aria-label={item.label}
                            >
                              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                              <span className="flex-1 text-left">{item.label}</span>
                            </button>
                            {expandedItems.has(item.label) && (
                              <div className="ml-4 mt-1 space-y-0.5">
                                {item.children!.map(child => (
                                  child.comingSoon ? (
                                    <div key={child.label} className="flex items-center justify-between rounded-lg px-3 py-1.5 text-xs text-muted-foreground opacity-60">
                                      <span>{child.label}</span>
                                      <Badge variant="secondary" className="text-[10px] px-1 py-0">Soon</Badge>
                                    </div>
                                  ) : (
                                    <Link
                                      key={child.href}
                                      to={child.href}
                                      className={cn(
                                        "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs transition-colors hover:bg-white/5",
                                        location.pathname === child.href ? "text-primary bg-primary/5" : "text-muted-foreground"
                                      )}
                                    >
                                      {child.label}
                                    </Link>
                                  )
                                ))}
                              </div>
                            )}
                          </>
                        ) : (
                          <Link
                            to={item.href}
                            className={cn(
                              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/5",
                              active ? "bg-primary/10 text-primary" : "text-muted-foreground"
                            )}
                            aria-label={item.label}
                          >
                            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                            <span>{item.label}</span>
                          </Link>
                        )}
                      </div>
                    )
                  })}
                </div>
              ))}
            </div>
          </aside>
        </div>
      )}

      <button
        className="fixed bottom-4 left-4 z-30 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white shadow-lg md:hidden"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
      >
        {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>
    </>
  )
}
