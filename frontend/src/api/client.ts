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

// Saved cohorts
export async function fetchSavedCohorts(): Promise<SavedCohort[]> {
  const { data } = await api.get<SavedCohort[]>('/cohorts/saved/')
  return data
}

export async function createSavedCohort(payload: { name: string; description: string; filters: CohortFilters }): Promise<SavedCohort> {
  const { data } = await api.post<SavedCohort>('/cohorts/saved/', payload)
  return data
}

export async function deleteSavedCohort(id: number): Promise<void> {
  await api.delete(`/cohorts/saved/${id}/`)
}

export function exportCohortUrl(id: number, format: 'csv' | 'json'): string {
  return `/api/cohorts/saved/${id}/export/?format=${format}`
}
