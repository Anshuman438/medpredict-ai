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

    <form className="form" onSubmit={handleSubmit}>
      <input
        name="email"
        type="email"
        placeholder="Email"
        onChange={handleChange}
        required
      />
      <input
        name="password"
        type="password"
        placeholder="Password"
        onChange={handleChange}
        required
      />

      <button className="primary-btn full-btn">
        Login
      </button>
    </form>

    <p className="auth-switch">
      Don’t have an account?{' '}
      <Link to="/register">Register</Link>
    </p>

  </AuthLayout>
)
}

export default Login