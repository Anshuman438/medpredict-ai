import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api'
})

api.interceptors.request.use((config) => {
  const user = JSON.parse(localStorage.getItem('user'))

  if (user?.token) {
    config.headers.Authorization = `Bearer ${user.token}`
  }

  return config
})

export default api