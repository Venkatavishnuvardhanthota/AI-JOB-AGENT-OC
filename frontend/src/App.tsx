import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { Navbar } from './components/Navbar'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { ProfilePage } from './pages/ProfilePage'
import { JobSearchPage } from './pages/JobSearchPage'
import { JobDetailPage } from './pages/JobDetailPage'
import { SavedJobsPage } from './pages/SavedJobsPage'

function HomePage() {
  return (
    <div>
      <h1>AI Job Application Agent</h1>
      <p>Welcome to the AI Job Application Agent. Use the search page to find and save jobs.</p>
    </div>
  )
}

function App() {
  return (
    <AuthProvider>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/jobs" element={<JobSearchPage />} />
        <Route path="/jobs/:id" element={<JobDetailPage />} />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/saved-jobs"
          element={
            <ProtectedRoute>
              <SavedJobsPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
