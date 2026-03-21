import { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'
import api from '../services/api'
import { AuthContext } from '../context/AuthContext'
import { Link } from 'react-router-dom'
function Login() {
  const [form, setForm] = useState({ email: '', password: '' })
  const { login } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      const { data } = await api.post('/auth/login', form)
      login(data)
      navigate('/dashboard')
    } catch (error) {
      alert('Login failed')
    }
  }

  return (
  <AuthLayout>
    <h2 className="form-title">Welcome Back</h2>
    <p className="form-subtitle">Secure access to your health intelligence</p>

    <form className="form" onSubmit={handleSubmit}>
      <div className="input-group">
        <label>Email Address</label>
        <input name="email" type="email" placeholder="e.g. user@example.com" onChange={handleChange} required />
      </div>
      <div className="input-group">
        <label>Password</label>
        <input name="password" type="password" placeholder="••••••••" onChange={handleChange} required />
      </div>
      <button className="primary-btn full-btn">Sign In</button>
    </form>

    <p className="auth-switch">
      New to MedPredict? <Link to="/register" className="auth-link">Create Account</Link>
    </p>

  </AuthLayout>
)
}

export default Login