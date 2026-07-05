import axios from 'axios'
import type { CohortFilters, FormSettings, MetricsResponse, SavedCohort } from '../types'

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/)
  return match ? match[1] : ''
}

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
})

api.interceptors.request.use(config => {
  const token = getCsrfToken()
  if (token) {
    config.headers['X-CSRFToken'] = token
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url: string = error.config?.url ?? ''
    const status: number = error.response?.status
    // On 401 (session expired) from non-auth endpoints, reload so useAuth
    // re-checks and shows LoginPage. 403 means "authorised but forbidden"
    // (e.g. non-Premium hitting export) — do NOT reload; let the caller handle it.
    if (status === 401 && !url.includes('/auth/')) {
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

function toParams(filters: CohortFilters): URLSearchParams {
  const p = new URLSearchParams()
  for (const [key, val] of Object.entries(filters)) {
    if (val === undefined || val === null || val === '') continue
    if (Array.isArray(val)) {
      val.forEach(v => p.append(key, String(v)))
    } else {
      p.set(key, String(val))
    }
  }
  return p
}

export async function fetchFormSettings(disease: string): Promise<FormSettings> {
  const { data } = await api.get<FormSettings>(`/form-settings/?disease=${encodeURIComponent(disease)}`)
  return data
}

export async function fetchMetrics(filters: CohortFilters): Promise<MetricsResponse> {
  const { data } = await api.get<MetricsResponse>(`/metrics/?${toParams(filters)}`)
  return data
}

// Auth
export async function fetchCurrentUser() {
  const { data } = await api.get('/auth/user/')
  return data
}

export async function login(email: string, password: string) {
  const { data } = await api.post('/auth/login/', { email, password })
  return data
}

export async function logout() {
  await api.post('/auth/logout/')
}

export async function signup(email: string, password: string, name: string) {
  const { data } = await api.post('/auth/signup/', { email, password, name })
  return data
}

export async function fetchOrganizations(): Promise<string[]> {
  const { data } = await api.get<string[]>('/auth/organizations/')
  return data
}

export async function fetchMyOrgs(): Promise<{ value: string; label: string }[]> {
  const { data } = await api.get<{ value: string; label: string }[]>('/auth/my-orgs/')
  return data
}

// Saved cohorts
export async function fetchSavedCohorts(): Promise<SavedCohort[]> {
  const { data } = await api.get<SavedCohort[]>('/cohorts/saved/')
  return data
}

export async function createSavedCohort(payload: { name: string; description: string; filters: CohortFilters }): Promise<SavedCohort> {
  const { data } = await api.post<SavedCohort>('/cohorts/saved/', payload)
  return data
}

export async function updateSavedCohort(id: number, payload: { name?: string; description?: string; filters?: CohortFilters }): Promise<SavedCohort> {
  const { data } = await api.put<SavedCohort>(`/cohorts/saved/${id}/`, payload)
  return data
}

export async function deleteSavedCohort(id: number): Promise<void> {
  await api.delete(`/cohorts/saved/${id}/`)
}

export default api
