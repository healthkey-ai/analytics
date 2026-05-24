import axios from 'axios'
import type { CohortFilters, FormSettings, MetricsResponse } from '../types'

const api = axios.create({ baseURL: '/api' })

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
