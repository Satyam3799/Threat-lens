import axios from 'axios'
import { clearAuthToken, getAuthToken, TOKEN_STORAGE_KEY } from '../utils/auth'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = getAuthToken()

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && getAuthToken()) {
      clearAuthToken()
      if (window.location.pathname !== '/login') {
        window.location.assign('/login')
      }
    }
    return Promise.reject(error)
  },
)

export { TOKEN_STORAGE_KEY }

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (payload) => api.post('/auth/register', payload),
}

export const scanApi = {
  run: (target) => api.post('/scan', { target }),
  history: (limit = 25) => api.get('/scan/history', { params: { limit } }),
  getById: (scanId) => api.get(`/scan/${scanId}`),
  getEnriched: (scanId) => api.get(`/scan/${scanId}/enriched`),
}

export default api
