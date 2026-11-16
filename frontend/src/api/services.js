import api from './client'

const d = (p) => p.then((r) => r.data)

export const authApi = {
  login: (email, password) => d(api.post('/auth/login', { email, password })),
  register: (body) => d(api.post('/auth/register', body)),
  me: () => d(api.get('/auth/me')),
  logout: () => d(api.post('/auth/logout')),
  forgot: (email) => d(api.post('/auth/forgot-password', { email })),
  reset: (token, new_password) => d(api.post('/auth/reset-password', { token, new_password })),
}

export const userApi = {
  update: (body) => d(api.put('/users/me', body)),
  changePassword: (body) => d(api.post('/users/me/change-password', body)),
}

export const metaApi = { options: () => d(api.get('/meta/options')) }

export const dashboardApi = { summary: () => d(api.get('/dashboard/summary')) }

export const applianceApi = {
  list: (params) => d(api.get('/appliances', { params })),
  get: (id) => d(api.get(`/appliances/${id}`)),
  create: (body) => d(api.post('/appliances', body)),
  update: (id, body) => d(api.put(`/appliances/${id}`, body)),
  remove: (id) => d(api.delete(`/appliances/${id}`)),
  uploadImage: (id, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return d(api.post(`/appliances/${id}/image`, fd))
  },
  removeImage: (id) => d(api.delete(`/appliances/${id}/image`)),
  addRecord: (id, body) => d(api.post(`/appliances/${id}/records`, body)),
  deleteRecord: (id, rid) => d(api.delete(`/appliances/${id}/records/${rid}`)),
}

export const predictionApi = {
  latest: () => d(api.get('/predictions/latest')),
  runAll: () => d(api.post('/predictions/run')),
  runOne: (id) => d(api.post(`/predictions/appliances/${id}`)),
  history: (params) => d(api.get('/predictions/history', { params })),
  modelInfo: () => d(api.get('/predictions/model-info')),
}

export const scheduleApi = {
  list: (params) => d(api.get('/schedules', { params })),
  create: (body) => d(api.post('/schedules', body)),
  update: (id, body) => d(api.put(`/schedules/${id}`, body)),
  setStatus: (id, body) => d(api.patch(`/schedules/${id}/status`, body)),
  cancel: (id) => d(api.post(`/schedules/${id}/cancel`)),
  remove: (id) => d(api.delete(`/schedules/${id}`)),
  suggestions: () => d(api.get('/schedules/suggestions')),
  accept: (appliance_id, scheduled_at) => d(api.post('/schedules/suggestions/accept', { appliance_id, scheduled_at })),
}

export const issueApi = {
  list: (params) => d(api.get('/issues', { params })),
  create: (body) => d(api.post('/issues', body)),
  update: (id, body) => d(api.put(`/issues/${id}`, body)),
  remove: (id) => d(api.delete(`/issues/${id}`)),
  uploadImage: (id, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return d(api.post(`/issues/${id}/image`, fd))
  },
}

export const expenseApi = {
  list: (params) => d(api.get('/expenses', { params })),
  create: (body) => d(api.post('/expenses', body)),
  update: (id, body) => d(api.put(`/expenses/${id}`, body)),
  remove: (id) => d(api.delete(`/expenses/${id}`)),
  summary: (year) => d(api.get('/expenses/summary', { params: { year } })),
}

export const notificationApi = {
  list: (params) => d(api.get('/notifications', { params })),
  unread: () => d(api.get('/notifications/unread-count')),
  refresh: () => d(api.post('/notifications/refresh')),
  markRead: (id, read = true) => d(api.patch(`/notifications/${id}/read`, null, { params: { read } })),
  readAll: () => d(api.post('/notifications/read-all')),
  remove: (id) => d(api.delete(`/notifications/${id}`)),
}

export const chatApi = {
  send: (message, session_id) => d(api.post('/chat', { message, session_id })),
  status: () => d(api.get('/chat/status')),
  sessions: () => d(api.get('/chat/sessions')),
  history: (session_id) => d(api.get('/chat/history', { params: { session_id } })),
  removeSession: (sid) => d(api.delete(`/chat/sessions/${sid}`)),
}
