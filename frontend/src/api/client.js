import axios from 'axios'

export const API_BASE = import.meta.env.VITE_API_BASE_URL || ''
const TOKEN_KEY = 'homecare_token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

const api = axios.create({ baseURL: `${API_BASE}/api`, timeout: 60000 })

api.interceptors.request.use((config) => {
  const t = tokenStore.get()
  if (t) config.headers.Authorization = `Bearer ${t}`
  return config
})

let onUnauthorized = () => {}
export const setUnauthorizedHandler = (fn) => { onUnauthorized = fn }

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && !error.config.url.startsWith('/auth/login')) {
      tokenStore.clear()
      onUnauthorized()
    }
    return Promise.reject(error)
  },
)

export function errorMessage(err, fallback = 'Something went wrong') {
  const d = err?.response?.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d)) return d.map((x) => x.msg).join('; ')
  if (err?.code === 'ECONNABORTED') return 'The server took too long to respond'
  if (!err?.response) return 'Cannot reach the server. Is the backend running?'
  return fallback
}

export const assetUrl = (path) => (path ? `${API_BASE}${path}` : null)

export default api
