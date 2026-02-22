import { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '../layouts/AuthLayout'
import api from '../services/api'
import { AuthContext } from '../context/AuthContext'

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
      alert('Registration failed')
    }
  }

  return (
    <AuthLayout>
      <h2 className="form-title">Create Account</h2>

      <form className="form" onSubmit={handleSubmit}>
        <input name="name" placeholder="Full Name" onChange={handleChange} />
        <input name="email" type="email" placeholder="Email" onChange={handleChange} />
        <input name="password" type="password" placeholder="Password" onChange={handleChange} />

        <button className="primary-btn full-btn">Register</button>
      </form>
    </AuthLayout>
  )
}

export default Register