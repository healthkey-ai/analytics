import { useState, useEffect } from 'react'
import type { CohortFilters, FormSettings } from '../../types'
import { fetchMyOrgs } from '../../api/client'
import SaveCohortModal from './SaveCohortModal'
import SavedCohortsList from './SavedCohortsList'

interface Props {
  filters: CohortFilters
  settings: FormSettings | null
  onUpdate: <K extends keyof CohortFilters>(key: K, val: CohortFilters[K]) => void
  onClear: () => void
  cohortCount: number
  onLoadCohort: (filters: CohortFilters, cohortId?: number, cohortName?: string) => void
  activeCohortName: string | null
  activeCohortId: number | null
  cohortDirty: boolean
}

function Section({ title, children, defaultOpen = true }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border-b border-slate-700">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex justify-between items-center px-4 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-700/50"
      >
        {title}
        <span className="text-slate-400">{open ? '−' : '+'}</span>
      </button>
      {open && <div className="px-4 pb-4 space-y-2">{children}</div>}
    </div>
  )
}

function MultiSelect({ options, selected, onChange, placeholder }: {
  options: string[]; selected: string[]; onChange: (v: string[]) => void; placeholder?: string
}) {
  const toggle = (v: string) =>
    onChange(selected.includes(v) ? selected.filter(x => x !== v) : [...selected, v])
  return (
    <div className="space-y-1 max-h-40 overflow-y-auto pr-1">
      {options.map(opt => (
        <label key={opt} className="flex items-center gap-2 cursor-pointer group">
          <input
            type="checkbox"
            checked={selected.includes(opt)}
            onChange={() => toggle(opt)}
            className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800"
          />
          <span className="text-xs text-slate-300 group-hover:text-white leading-tight">{opt}</span>
        </label>
      ))}
      {options.length === 0 && <p className="text-xs text-slate-500 italic">{placeholder ?? 'No options'}</p>}
    </div>
  )
}

function RangeInputs({ label, minKey, maxKey, filters, onUpdate, step = 1 }: {
  label: string
  minKey: keyof CohortFilters
  maxKey: keyof CohortFilters
  filters: CohortFilters
  onUpdate: <K extends keyof CohortFilters>(k: K, v: CohortFilters[K]) => void
  step?: number
}) {
  return (
    <div>
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <div className="flex gap-2">
        <input
          type="number"
          step={step}
          placeholder="Min"
          value={(filters[minKey] as number | undefined) ?? ''}
          onChange={e => onUpdate(minKey, e.target.value ? Number(e.target.value) as never : undefined as never)}
          className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
        />
        <input
          type="number"
          step={step}
          placeholder="Max"
          value={(filters[maxKey] as number | undefined) ?? ''}
          onChange={e => onUpdate(maxKey, e.target.value ? Number(e.target.value) as never : undefined as never)}
          className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500"
        />
      </div>
    </div>
  )
}

export default function CohortPanel({ filters, settings, onUpdate, onClear, cohortCount, onLoadCohort, activeCohortName, activeCohortId, cohortDirty }: Props) {
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [savedRefresh, setSavedRefresh] = useState(0)
  const [orgOptions, setOrgOptions] = useState<{ value: string; label: string }[]>([])

  useEffect(() => {
    fetchMyOrgs().then(setOrgOptions).catch(() => {})
  }, [])

  const sel = <K extends keyof CohortFilters>(key: K) => (filters[key] as string[] | undefined) ?? []
  const upd = <K extends keyof CohortFilters>(key: K) => (v: string[]) =>
    onUpdate(key, v.length ? v as never : undefined as never)

  const isMM = filters.disease === 'Multiple Myeloma'

  return (
    <aside className="w-72 shrink-0 bg-slate-800 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-4 py-4 border-b border-slate-700">
        <h2 className="text-base font-bold text-white">Cohort Builder</h2>
        <p className="text-xs text-slate-400 mt-0.5">Filter patients below</p>
      </div>

      {/* Active cohort indicator */}
      {activeCohortName && (
        <div className={`px-4 py-2 border-b flex items-center gap-2 ${cohortDirty ? 'bg-amber-900/30 border-amber-700/50' : 'bg-teal-900/40 border-teal-700/50'}`}>
          <span className={`text-xs font-medium truncate ${cohortDirty ? 'text-amber-400' : 'text-teal-400'}`}>
            {cohortDirty ? 'Modified:' : 'Active:'} {activeCohortName}
          </span>
        </div>
      )}

      {/* Cohort badge + save button */}
      <div className="px-4 py-3 bg-slate-900/50 border-b border-slate-700 flex items-center justify-between gap-2">
        <div>
          <span className="text-sm text-slate-300">Patients selected</span>
          <span className="ml-2 bg-teal-500 text-white text-sm font-bold px-3 py-0.5 rounded-full">
            {cohortCount.toLocaleString()}
          </span>
        </div>
        <button
          onClick={() => setShowSaveModal(true)}
          className="text-xs bg-teal-700 hover:bg-teal-600 text-white font-medium px-2.5 py-1 rounded transition-colors shrink-0"
          title="Save current filters as a cohort"
        >
          Save
        </button>
      </div>

      {/* Scrollable filters */}
      <div className="flex-1 overflow-y-auto">

        <Section title="Organization">
          <select
            value={filters.org ?? ''}
            onChange={e => onUpdate('org', e.target.value || undefined)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-teal-500"
          >
            <option value="">All</option>
            {orgOptions.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </Section>

        <Section title="Saved Cohorts" defaultOpen={false}>
          <SavedCohortsList onLoad={(f, id, name) => onLoadCohort(f, id, name)} refreshToken={savedRefresh} />
        </Section>

        <Section title="Disease">
          <select
            value={filters.disease ?? ''}
            onChange={e => onUpdate('disease', e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1.5 text-sm text-white focus:outline-none focus:border-teal-500"
          >
            {(settings?.diseases ?? ['Multiple Myeloma', 'Breast Cancer']).map(d => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </Section>

        <Section title="Stage">
          <MultiSelect
            options={settings?.stages ?? []}
            selected={sel('stage')}
            onChange={upd('stage')}
          />
        </Section>

        <Section title="Demographics">
          <RangeInputs label="Age" minKey="age_min" maxKey="age_max" filters={filters} onUpdate={onUpdate} />
          <div>
            <p className="text-xs text-slate-400 mb-1">Gender</p>
            <div className="flex gap-3">
              {['M', 'F'].map(g => (
                <label key={g} className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name="gender"
                    checked={filters.gender === g}
                    onChange={() => onUpdate('gender', g)}
                    className="text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800"
                  />
                  <span className="text-xs text-slate-300">{g === 'M' ? 'Male' : 'Female'}</span>
                </label>
              ))}
              {filters.gender && (
                <button onClick={() => onUpdate('gender', undefined)} className="text-xs text-slate-500 hover:text-red-400">✕</button>
              )}
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">Race</p>
            <MultiSelect options={settings?.race_options ?? []} selected={sel('race')} onChange={upd('race')} />
          </div>
        </Section>

        <Section title="Performance Status" defaultOpen={false}>
          <div>
            <p className="text-xs text-slate-400 mb-1">ECOG</p>
            <div className="flex gap-2 flex-wrap">
              {[0, 1, 2, 3].map(e => {
                const cur = (filters.ecog ?? [])
                const selected = cur.includes(e)
                return (
                  <button
                    key={e}
                    onClick={() => onUpdate('ecog', selected ? cur.filter(x => x !== e) : [...cur, e])}
                    className={`px-2 py-0.5 rounded text-xs font-medium border transition-colors ${selected ? 'bg-teal-500 border-teal-500 text-white' : 'border-slate-600 text-slate-400 hover:border-teal-500'}`}
                  >
                    ECOG {e}
                  </button>
                )
              })}
            </div>
          </div>
        </Section>

        {isMM && (
          <Section title="Cytogenetics / Molecular" defaultOpen={false}>
            <MultiSelect
              options={settings?.cytogenetic_markers ?? []}
              selected={sel('cytogenetic_markers')}
              onChange={upd('cytogenetic_markers')}
            />
            <div className="flex items-center gap-2 mt-1">
              <input
                type="checkbox"
                id="high_risk"
                checked={filters.high_risk_cytogenetics === true}
                onChange={e => onUpdate('high_risk_cytogenetics', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800"
              />
              <label htmlFor="high_risk" className="text-xs text-slate-300 cursor-pointer">High-risk only (del17p, t4;14, t14;16)</label>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="tp53"
                checked={filters.tp53_disruption === true}
                onChange={e => onUpdate('tp53_disruption', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800"
              />
              <label htmlFor="tp53" className="text-xs text-slate-300 cursor-pointer">TP53 disruption</label>
            </div>
          </Section>
        )}

        <Section title="Treatment History" defaultOpen={false}>
          <div>
            <p className="text-xs text-slate-400 mb-1">Therapy lines</p>
            <div className="flex gap-2">
              <select
                value={filters.therapy_lines_min ?? ''}
                onChange={e => onUpdate('therapy_lines_min', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="">Min</option>
                {[1,2,3,4].map(n => <option key={n} value={n}>{n}L</option>)}
              </select>
              <select
                value={filters.therapy_lines_max ?? ''}
                onChange={e => onUpdate('therapy_lines_max', e.target.value ? Number(e.target.value) : undefined)}
                className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white focus:outline-none focus:border-teal-500"
              >
                <option value="">Max</option>
                {[1,2,3,4].map(n => <option key={n} value={n}>{n}L</option>)}
              </select>
            </div>
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">1L Regimen</p>
            <MultiSelect options={settings?.first_line_therapies ?? []} selected={sel('first_line_therapy')} onChange={upd('first_line_therapy')} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">1L Outcome</p>
            <MultiSelect options={settings?.outcome_options ?? []} selected={sel('first_line_outcome')} onChange={upd('first_line_outcome')} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">2L Regimen</p>
            <MultiSelect options={settings?.second_line_therapies ?? []} selected={sel('second_line_therapy')} onChange={upd('second_line_therapy')} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">2L Outcome</p>
            <MultiSelect options={settings?.outcome_options ?? []} selected={sel('second_line_outcome')} onChange={upd('second_line_outcome')} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">3L+ Regimen</p>
            <MultiSelect options={settings?.later_line_therapies ?? []} selected={sel('later_therapy')} onChange={upd('later_therapy')} />
          </div>
          <div>
            <p className="text-xs text-slate-400 mb-1">3L+ Outcome</p>
            <MultiSelect options={settings?.outcome_options ?? []} selected={sel('later_outcome')} onChange={upd('later_outcome')} />
          </div>
        </Section>

        <Section title="Refractory Status" defaultOpen={false}>
          <MultiSelect
            options={settings?.refractory_statuses ?? []}
            selected={sel('refractory_status')}
            onChange={upd('refractory_status')}
          />
        </Section>

        {isMM && (
          <Section title="MM Characteristics" defaultOpen={false}>
            <div>
              <p className="text-xs text-slate-400 mb-1">MRD Status</p>
              <MultiSelect
                options={settings?.mrd_status_options ?? ['MRD Negative', 'MRD Positive', 'Not Assessed']}
                selected={sel('mrd_status')}
                onChange={upd('mrd_status')}
              />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={filters.meets_crab === true}
                onChange={e => onUpdate('meets_crab', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800" />
              <span className="text-xs text-slate-300">CRAB criteria met</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={filters.has_bone_lesions === true}
                onChange={e => onUpdate('has_bone_lesions', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800" />
              <span className="text-xs text-slate-300">Bone lesions present</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={filters.has_sct === true}
                onChange={e => onUpdate('has_sct', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800" />
              <span className="text-xs text-slate-300">Prior ASCT</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={filters.plasma_cell_leukemia === true}
                onChange={e => onUpdate('plasma_cell_leukemia', e.target.checked ? true : undefined)}
                className="rounded border-slate-500 bg-slate-700 text-teal-500 focus:ring-teal-500 focus:ring-offset-slate-800" />
              <span className="text-xs text-slate-300">Plasma cell leukemia</span>
            </label>
          </Section>
        )}

        <Section title="Lab Values" defaultOpen={false}>
          <RangeInputs label="Hemoglobin (g/dL)" minKey="hemoglobin_min" maxKey="hemoglobin_max" filters={filters} onUpdate={onUpdate} step={0.5} />
          <div>
            <p className="text-xs text-slate-400 mb-1">Creatinine max (mg/dL)</p>
            <input type="number" step={0.1} placeholder="e.g. 2.0"
              value={filters.creatinine_max ?? ''}
              onChange={e => onUpdate('creatinine_max', e.target.value ? Number(e.target.value) : undefined)}
              className="w-full bg-slate-700 border border-slate-600 rounded px-2 py-1 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-teal-500" />
          </div>
          <RangeInputs label="β2-Microglobulin (mg/L)" minKey="b2m_min" maxKey="b2m_max" filters={filters} onUpdate={onUpdate} step={0.5} />
        </Section>

        <Section title="Lifestyle" defaultOpen={false}>
          <div>
            <p className="text-xs text-slate-400 mb-1">Smoking status</p>
            <MultiSelect options={['Never', 'Former', 'Current']} selected={sel('smoking_status')} onChange={upd('smoking_status')} />
          </div>
        </Section>

      </div>

      {/* Clear button */}
      <div className="px-4 py-3 border-t border-slate-700">
        <button
          onClick={onClear}
          className="w-full text-sm text-slate-400 hover:text-red-400 hover:bg-slate-700/50 rounded px-3 py-1.5 transition-colors"
        >
          Clear all filters
        </button>
      </div>

      {showSaveModal && (
        <SaveCohortModal
          filters={filters}
          activeCohortId={activeCohortId ?? undefined}
          activeCohortName={activeCohortName ?? undefined}
          onSaved={(cohort) => { setShowSaveModal(false); setSavedRefresh(r => r + 1); onLoadCohort(cohort.filters, cohort.id, cohort.name) }}
          onClose={() => setShowSaveModal(false)}
        />
      )}
    </aside>
  )
}
