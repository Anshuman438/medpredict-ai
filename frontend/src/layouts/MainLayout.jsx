import { useState, useContext } from 'react'
import { Link, useNavigate,useLocation } from 'react-router-dom'
import { AuthContext } from '../context/AuthContext'

function MainLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const { user, logout } = useContext(AuthContext)
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/dashboard': return 'Dashboard Overview'
      case '/symptoms': return 'AI Symptom Analysis'
      case '/chat': return 'Medical AI Assistant'
      case '/history': return 'Prediction History'
      case '/notes': return 'Wellness Notes'
      default: return 'MedPredict AI'
    }
  }

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: '🏠' },
    { path: '/symptoms', label: 'Symptom Checker', icon: '🩺' },
    { path: '/chat', label: 'AI Chat', icon: '💬' },
    { path: '/history', label: 'History', icon: '📜' },
    { path: '/notes', label: 'Notes', icon: '📝' },
  ]

  return (
    <div className="app-layout">

      {sidebarOpen && (
        <div 
          className="overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <div className="brand-icon">M</div>
          <span className="logo-text">MedPredict</span>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link 
              key={item.path}
              to={item.path} 
              className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
              onClick={() => setSidebarOpen(false)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile-sm">
            <div className="avatar">{user?.name?.charAt(0) || 'U'}</div>
            <div className="user-info">
              <p className="user-name">Hello, {user?.name || 'User'}</p>
            </div>
          </div>
          <button className="sidebar-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </aside>

      <div className="main-content">
        <header className="top-navbar">
          <button 
            className="menu-btn"
            onClick={() => setSidebarOpen(true)}
          >
            ☰
          </button>
          <h3 className="nav-welcome">{getPageTitle()}</h3>
          <div className="navbar-actions">
            <div className="notif-bell">🔔</div>
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