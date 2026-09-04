import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './context/AuthContext'
import { ToastProvider } from '@/components/ui/toast'
import { AppLayout } from '@/components/layout/app-layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { GuestRoute } from './components/GuestRoute'
import { ErrorBoundary } from '@/components/layout/error-boundary'
import { AuthLoader } from '@/components/layout/loading-skeletons'

const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })))
const RegisterPage = lazy(() => import('./pages/RegisterPage').then(m => ({ default: m.RegisterPage })))
const ForgotPasswordPage = lazy(() => import('./pages/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })))
const ResetPasswordPage = lazy(() => import('./pages/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })))
const VerifyEmailPage = lazy(() => import('./pages/VerifyEmailPage').then(m => ({ default: m.VerifyEmailPage })))
const AuthSecurityPage = lazy(() => import('./pages/AuthSecurityPage').then(m => ({ default: m.AuthSecurityPage })))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })))
const ErrorPage = lazy(() => import('./pages/ErrorPage').then(m => ({ default: m.ErrorPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })))
const ApplicationsPage = lazy(() => import('./pages/ApplicationsPage').then(m => ({ default: m.ApplicationsPage })))
const ApplicationDetailPage = lazy(() => import('./pages/ApplicationDetailPage').then(m => ({ default: m.ApplicationDetailPage })))
const KanbanPage = lazy(() => import('./pages/KanbanPage').then(m => ({ default: m.KanbanPage })))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })))
const CalendarPage = lazy(() => import('./pages/CalendarPage').then(m => ({ default: m.CalendarPage })))
const ProductionDashboardPage = lazy(() => import('./pages/ProductionDashboardPage').then(m => ({ default: m.ProductionDashboardPage })))
const DiscoveryPage = lazy(() => import('./pages/DiscoveryPage').then(m => ({ default: m.DiscoveryPage })))
const MatchingPage = lazy(() => import('./pages/MatchingPage').then(m => ({ default: m.MatchingPage })))
const JobsSearchPage = lazy(() => import('./pages/JobsSearchPage').then(m => ({ default: m.JobsSearchPage })))
const SavedJobsPage = lazy(() => import('./pages/SavedJobsPage').then(m => ({ default: m.SavedJobsPage })))
const JobDetailPage = lazy(() => import('./pages/JobDetailPage').then(m => ({ default: m.JobDetailPage })))
const ResumeLibraryPage = lazy(() => import('./pages/ResumeLibraryPage').then(m => ({ default: m.ResumeLibraryPage })))
const ResumeDetailPage = lazy(() => import('./pages/ResumeDetailPage').then(m => ({ default: m.ResumeDetailPage })))
const CoverLettersPage = lazy(() => import('./pages/CoverLettersPage').then(m => ({ default: m.CoverLettersPage })))
const CoverLetterDetailPage = lazy(() => import('./pages/CoverLetterDetailPage').then(m => ({ default: m.CoverLetterDetailPage })))
const BrowserSessionsPage = lazy(() => import('./pages/BrowserSessionsPage').then(m => ({ default: m.BrowserSessionsPage })))
const ApplicationGenerationPage = lazy(() => import('./pages/ApplicationGenerationPage').then(m => ({ default: m.ApplicationGenerationPage })))
const OrchestrationPage = lazy(() => import('./pages/OrchestrationPage').then(m => ({ default: m.OrchestrationPage })))
const CareerProfilePage = lazy(() => import('./pages/CareerProfilePage').then(m => ({ default: m.CareerProfilePage })))
const SettingsAccountPage = lazy(() => import('./pages/SettingsAccountPage').then(m => ({ default: m.SettingsAccountPage })))
const SettingsPreferencesPage = lazy(() => import('./pages/SettingsPreferencesPage').then(m => ({ default: m.SettingsPreferencesPage })))
const AISettingsPage = lazy(() => import('./pages/AISettingsPage').then(m => ({ default: m.AISettingsPage })))
const ProviderManagementPage = lazy(() => import('./pages/ProviderManagementPage').then(m => ({ default: m.ProviderManagementPage })))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30000,
      retry: 1,
    },
  },
})

function LoadingFallback() {
  return <AuthLoader />
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <ErrorBoundary>
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/login" element={<GuestRoute><LoginPage /></GuestRoute>} />
                <Route path="/register" element={<GuestRoute><RegisterPage /></GuestRoute>} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
                <Route path="/verify-email" element={<VerifyEmailPage />} />
                <Route path="/auth/security" element={<AuthSecurityPage />} />
                <Route path="/error" element={<ErrorPage />} />

                <Route
                  element={
                    <ProtectedRoute>
                      <AppLayout />
                    </ProtectedRoute>
                  }
                >
                  <Route path="/dashboard" element={<DashboardPage />} />
                  <Route path="/applications" element={<ApplicationsPage />} />
                  <Route path="/applications/board" element={<KanbanPage />} />
                  <Route path="/analytics" element={<AnalyticsPage />} />
                  <Route path="/calendar" element={<CalendarPage />} />
                  <Route path="/production" element={<ProductionDashboardPage />} />
                  <Route path="/discovery" element={<DiscoveryPage />} />
                  <Route path="/matching" element={<MatchingPage />} />
                  <Route path="/applications/:id" element={<ApplicationDetailPage />} />
                  <Route path="/applications/:id/*" element={<ApplicationDetailPage />} />
                  <Route path="/jobs/search" element={<JobsSearchPage />} />
                  <Route path="/jobs/saved" element={<SavedJobsPage />} />
                  <Route path="/jobs/:id" element={<JobDetailPage />} />
                  <Route path="/resumes" element={<ResumeLibraryPage />} />
                  <Route path="/resumes/:id" element={<ResumeDetailPage />} />
                  <Route path="/cover-letters" element={<CoverLettersPage />} />
                  <Route path="/cover-letters/:id" element={<CoverLetterDetailPage />} />
                  <Route path="/browser" element={<BrowserSessionsPage />} />
                  <Route path="/application-generation" element={<ApplicationGenerationPage />} />
                  <Route path="/orchestration" element={<OrchestrationPage />} />
                  <Route path="/profile" element={<CareerProfilePage />} />
                  <Route path="/settings/account" element={<SettingsAccountPage />} />
                  <Route path="/settings/preferences" element={<SettingsPreferencesPage />} />
                  <Route path="/settings/ai" element={<AISettingsPage />} />
                  <Route path="/providers" element={<ProviderManagementPage />} />
                  <Route path="/" element={<Navigate to="/dashboard" replace />} />
                </Route>

                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </ErrorBoundary>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
