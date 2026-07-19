import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <nav>
      <div>
        <Link to="/">AI Job Agent</Link>
        <div>
          {isAuthenticated ? (
            <>
              <Link to="/jobs">Search Jobs</Link>
              <Link to="/saved-jobs">Saved Jobs</Link>
              <Link to="/profile">Profile</Link>
              <span>{user?.email}</span>
              <button onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <Link to="/login">Login</Link>
              <Link to="/register">Register</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
