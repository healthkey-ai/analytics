export interface CohortFilters {
  disease?: string
  stage?: string[]
  age_min?: number
  age_max?: number
  gender?: string
  ethnicity?: string[]
  region?: string[]
  ecog?: number[]
  cytogenetic_markers?: string[]
  high_risk_cytogenetics?: boolean
  tp53_disruption?: boolean
  first_line_therapy?: string[]
  second_line_therapy?: string[]
  later_therapy?: string[]
  first_line_outcome?: string[]
  second_line_outcome?: string[]
  later_outcome?: string[]
  refractory_status?: string[]
  therapy_lines_min?: number
  therapy_lines_max?: number
  has_sct?: boolean
  meets_crab?: boolean
  has_bone_lesions?: boolean
  plasma_cell_leukemia?: boolean
  diagnosis_year_min?: number
  diagnosis_year_max?: number
  smoking_status?: string[]
  hemoglobin_min?: number
  hemoglobin_max?: number
  creatinine_max?: number
  b2m_min?: number
  b2m_max?: number
  er_status?: string[]
  her2_status?: string[]
  tnbc_status?: boolean
}

export interface FormSettings {
  diseases: string[]
  stages: string[]
  first_line_therapies: string[]
  second_line_therapies: string[]
  later_line_therapies: string[]
  outcome_options: string[]
  cytogenetic_markers: string[]
  refractory_statuses: string[]
  regions: string[]
  ethnicity_options: string[]
  ecog_values: number[]
  smoking_options: string[]
  therapy_line_options: number[]
  extra_filters?: {
    mm_specific?: boolean
    bc_specific?: boolean
    has_sct_filter?: boolean
    crab_filter?: boolean
    er_pr_her2?: boolean
  }
}

export interface TherapyOutcomes {
  therapy: string
  outcomes: Record<string, number>
  total: number
  orr_pct: number
}

export interface TherapyCount {
  therapy: string
  count: number
  pct: number
}

export interface LabStats {
  median: number
  q1: number
  q3: number
  min: number
  max: number
  n: number
  unit: string
  label: string
}

export interface TreatmentDurationRow {
  therapy: string
  outcome: string
  median_months: number
  mean_months: number
  count: number
}

export interface MetricsResponse {
  cohort: { count: number }
  response_rates: {
    first_line: TherapyOutcomes[]
    second_line: TherapyOutcomes[]
    later_line: TherapyOutcomes[]
  }
  treatment_patterns: {
    first_line: TherapyCount[]
    second_line: TherapyCount[]
    later_line: TherapyCount[]
    line_funnel: { line: number; label: string; count: number; pct: number }[]
    line_distribution: { lines: number; label: string; count: number; pct: number }[]
    sequences: { sequence: string; count: number }[]
  }
  demographics: {
    age_distribution: { bucket: string; count: number; pct: number }[]
    gender: { gender: string; count: number; pct: number }[]
    race: { race: string; count: number; pct: number }[]
    ethnicity: { ethnicity: string; count: number; pct: number }[]
    region: { region: string; count: number }[]
    smoking: { status: string; count: number; pct: number }[]
  }
  staging: {
    stages: { stage: string; count: number; pct: number }[]
    ecog: { ecog: number; count: number; pct: number }[]
    crab: { label: string; count: number; pct: number }[]
    cytogenetics: { marker: string; count: number; pct: number; high_risk: boolean }[]
    sct_count: number
    sct_pct: number
    bone_lesions: { type: string; count: number; pct: number }[]
    refractory_status: { status: string; count: number; pct: number }[]
  }
  labs: Record<string, LabStats>
  treatment_duration: {
    first_line: TreatmentDurationRow[]
    second_line: TreatmentDurationRow[]
    later_line: TreatmentDurationRow[]
    time_to_first_treatment: {
      median_days: number
      distribution: { bucket: string; count: number }[]
    }
  }
  survival: {
    first_line:  SurvivalLine
    second_line: SurvivalLine
    later_line:  SurvivalLine
  }
}

export interface SurvivalLine {
  curve: { time: number; survival: number; at_risk: number }[]
  n: number
  median_pfs: number | null
}
