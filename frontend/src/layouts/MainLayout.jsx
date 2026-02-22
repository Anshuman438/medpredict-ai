import { useState, useContext } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'

function MainLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { user, logout } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="app-layout">

      {sidebarOpen && (
        <div 
          className="overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="logo">
          MedPredict
        </div>

        <nav>
          <Link to="/dashboard" onClick={() => setSidebarOpen(false)}>Dashboard</Link>
          <Link to="/symptoms" onClick={() => setSidebarOpen(false)}>Symptom Checker</Link>
          <Link to="/chat" onClick={() => setSidebarOpen(false)}>AI Chat</Link>
          <Link to="/history" onClick={() => setSidebarOpen(false)}>History</Link>
          <Link to="/notes" onClick={() => setSidebarOpen(false)}>Notes</Link>
        </nav>
      </aside>

      <div className="main-content">

        <header className="top-navbar">
          <button 
            className="menu-btn"
            onClick={() => setSidebarOpen(true)}
          >
            ☰
          </button>

          <h3>Welcome {user?.name || 'User'}</h3>

          <div className="navbar-actions">
            <button className="logout-btn" onClick={handleLogout}>
              Logout
            </button>
          </div>
        </header>

        <div className="content-area">
          {children}
        </div>

      </div>

    </div>
  )
}

export default MainLayout