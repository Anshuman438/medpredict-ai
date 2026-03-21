import { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'
import api from '../services/api'
import { AuthContext } from '../context/AuthContext'
import { Link } from 'react-router-dom'

function Register() {
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const { login } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    try {
      const { data } = await api.post('/auth/register', form)
      login(data)
      navigate('/dashboard')
    } catch (error) {
      console.log(error.response.data)
      alert(error.response?.data?.message || "Registration failed")
    }
  }

  return (
    <AuthLayout>
      <h2 className="form-title">Join MedPredict</h2>
      <p className="form-subtitle">Start your AI-powered wellness journey</p>

      <form className="form" onSubmit={handleSubmit}>
        <div className="input-group">
          <label>Full Name</label>
          <input name="name" placeholder="Your Name" onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label>Email Address</label>
          <input name="email" type="email" placeholder="user@example.com" onChange={handleChange} required />
        </div>
        <div className="input-group">
          <label>Password</label>
          <input name="password" type="password" placeholder="Create a strong password" onChange={handleChange} required />
        </div>
        <button className="primary-btn full-btn">Create Free Account</button>
      </form>

      <p className="auth-switch">
        Already a member? <Link to="/login" className="auth-link">Login Here</Link>
      </p>
    </AuthLayout>
  )
}

export default Register