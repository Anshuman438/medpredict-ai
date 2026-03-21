function AuthLayout({ children }) {
  return (
    <div className="auth-page-container">
      <div className="auth-glass-card">
        <div className="auth-brand">
          <div className="brand-dot"></div>
          <h2 className="cursor" onClick={() => {
            window.location.href = '/'
          }}>MedPredict AI</h2>
        </div>
        {children}
      </div>
    </div>
  )
}

export default AuthLayout