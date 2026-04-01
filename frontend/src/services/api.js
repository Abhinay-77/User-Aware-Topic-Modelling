import axios from 'axios'

const API_BASE_URL = "http://localhost:8001/api"

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  signup: (data) => api.post('/auth/signup', data),
  login:  (data) => api.post('/auth/login', data),
  getMe:  ()     => api.get('/auth/me'),
}

export const translationAPI = {
  translate:       (data) => api.post('/translation/translate', data),
  getHistory:      (limit = 10) => api.get(`/translation/history?limit=${limit}`),
  convertTanglish: (data) => api.post('/translation/tanglish', data),
  transliterate:   (data) => api.post('/translation/transliterate', data),
  transliterateBulk: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post('/translation/transliterate-bulk', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'text',
    })
  },
}

export const topicAPI = {
  runModeling:    (data) => api.post('/topic/run', data),
  analyzeText:    (data) => api.post('/topic/analyze-text', data),
  uploadDataset:  (formData) => api.post('/topic/upload-dataset', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getDatasets:    () => api.get('/topic/datasets'),
  getResults:     (limit = 5) => api.get(`/topic/results?limit=${limit}`),
  downloadResults:(resultId, format = 'csv') =>
    api.get(`/topic/download/${resultId}?format=${format}`, { responseType: 'blob' }),
  // NEW
  getUserProfile: (userId) => api.get(`/topic/user-profile/${userId}`),
  getUserDrift:   (userId) => api.get(`/topic/drift/${userId}`),
  getCorpusStats: ()       => api.get('/topic/corpus-stats'),
}

export const dashboardAPI = {
  getUserDashboard:      () => api.get('/dashboard/user'),
  getResearcherDashboard:() => api.get('/dashboard/researcher'),
  getAnalystDashboard:  () => api.get('/dashboard/analyst'),
  getBusinessDashboard: () => api.get('/dashboard/business'),
  uploadTopicsCSV:       (formData) => api.post('/dashboard/analyst/upload-topics-csv', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  analyzeSocialMedia:    (formData) => api.post('/dashboard/analyst/analyze-social-media', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
}

export default api
