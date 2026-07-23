import { Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from '@/components/ui/toast'
import { AppLayout } from '@/components/layout/app-layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { DashboardPage } from './pages/DashboardPage'
import { ApplicationsPage } from './pages/ApplicationsPage'
import { JobsSearchPage } from './pages/JobsSearchPage'
import { SavedJobsPage } from './pages/SavedJobsPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { ResumeLibraryPage } from './pages/ResumeLibraryPage'
import { CareerProfilePage } from './pages/CareerProfilePage'
import { WorkflowMonitorPage } from './pages/WorkflowMonitorPage'
import { OrchestrationsPage } from './pages/OrchestrationsPage'
import { ExecutionHistoryPage } from './pages/ExecutionHistoryPage'
import { OperationsPage } from './pages/OperationsPage'
import { ReportsPage } from './pages/ReportsPage'
import { BrowserSessionsPage } from './pages/BrowserSessionsPage'
import { ProvidersPage } from './pages/ProvidersPage'
import { LogsPage } from './pages/LogsPage'
import { SettingsAccountPage } from './pages/SettingsAccountPage'
import { SettingsPreferencesPage } from './pages/SettingsPreferencesPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              element={
                <ProtectedRoute>
                  <AppLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/applications" element={<ApplicationsPage />} />
              <Route path="/jobs/search" element={<JobsSearchPage />} />
              <Route path="/jobs/saved" element={<SavedJobsPage />} />
              <Route path="/jobs/:id" element={<JobDetailPage />} />
              <Route path="/resumes" element={<ResumeLibraryPage />} />
              <Route path="/profile" element={<CareerProfilePage />} />
              <Route path="/workflows/monitor" element={<WorkflowMonitorPage />} />
              <Route path="/workflows/orchestrations" element={<OrchestrationsPage />} />
              <Route path="/workflows/history" element={<ExecutionHistoryPage />} />
              <Route path="/infrastructure/operations" element={<OperationsPage />} />
              <Route path="/infrastructure/browser-sessions" element={<BrowserSessionsPage />} />
              <Route path="/infrastructure/providers" element={<ProvidersPage />} />
              <Route path="/infrastructure/logs" element={<LogsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/settings/account" element={<SettingsAccountPage />} />
              <Route path="/settings/preferences" element={<SettingsPreferencesPage />} />
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
            </Route>
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
