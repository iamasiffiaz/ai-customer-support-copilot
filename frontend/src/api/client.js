import axios from 'axios'

/** Empty baseURL uses Vite `/api` proxy in development (avoids CORS). */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export function getErrorMessage(error, fallback = 'Something went wrong') {
  return error?.response?.data?.detail || error?.message || fallback
}

export const ticketsApi = {
  list: (params) => api.get('/api/tickets', { params }).then((r) => r.data),
  get: (id) => api.get(`/api/tickets/${id}`).then((r) => r.data),
  create: (data) => api.post('/api/tickets', data).then((r) => r.data),
  update: (id, data) => api.put(`/api/tickets/${id}`, data).then((r) => r.data),
  remove: (id) => api.delete(`/api/tickets/${id}`).then((r) => r.data),
}

export const analysisApi = {
  analyze: (id) => api.post(`/api/analysis/analyze-ticket/${id}`).then((r) => r.data),
  get: (id) => api.get(`/api/analysis/${id}`).then((r) => r.data),
  bulk: (ticket_ids) => api.post('/api/analysis/bulk-analyze', { ticket_ids }).then((r) => r.data),
}

export const repliesApi = {
  list: (params) => api.get('/api/replies', { params }).then((r) => r.data),
  generate: (ticketId, tone) =>
    api.post(`/api/replies/generate/${ticketId}`, { tone }).then((r) => r.data),
  update: (id, data) => api.put(`/api/replies/${id}`, data).then((r) => r.data),
  approve: (id) => api.post(`/api/replies/${id}/approve`).then((r) => r.data),
  markSent: (id) => api.post(`/api/replies/${id}/mark-sent`).then((r) => r.data),
  remove: (id) => api.delete(`/api/replies/${id}`).then((r) => r.data),
}

export const escalationsApi = {
  list: () => api.get('/api/escalations').then((r) => r.data),
  check: (ticketId) => api.post(`/api/escalations/check/${ticketId}`).then((r) => r.data),
  update: (id, data) => api.put(`/api/escalations/${id}`, data).then((r) => r.data),
  resolve: (id) => api.post(`/api/escalations/${id}/resolve`).then((r) => r.data),
}

export const kbApi = {
  documents: () => api.get('/api/knowledge-base/documents').then((r) => r.data),
  get: (id) => api.get(`/api/knowledge-base/documents/${id}`).then((r) => r.data),
  remove: (id) => api.delete(`/api/knowledge-base/documents/${id}`).then((r) => r.data),
  search: (query, limit = 5) =>
    api.post('/api/knowledge-base/search', { query, limit }).then((r) => r.data),
  upload: (file, title) => {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    return api
      .post('/api/knowledge-base/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },
}

export const copilotApi = {
  ask: (question, session_id) =>
    api.post('/api/copilot-chat/ask', { question, session_id }).then((r) => r.data),
  sessions: () => api.get('/api/copilot-chat/sessions').then((r) => r.data),
  session: (id) => api.get(`/api/copilot-chat/sessions/${id}`).then((r) => r.data),
}

export const analyticsApi = {
  dashboard: () => api.get('/api/analytics/dashboard').then((r) => r.data),
  tickets: () => api.get('/api/analytics/tickets').then((r) => r.data),
  responseTimes: () => api.get('/api/analytics/response-times').then((r) => r.data),
}

export const recommendationsApi = {
  list: () => api.get('/api/recommendations').then((r) => r.data),
  generate: () => api.post('/api/recommendations/generate').then((r) => r.data),
}

export const settingsApi = {
  get: () => api.get('/api/settings').then((r) => r.data),
  update: (data) => api.put('/api/settings', data).then((r) => r.data),
}

export default api
