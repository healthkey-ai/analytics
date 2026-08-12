import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StagingPanel from '../StagingPanel'

const mmData = {
  stages: [{ stage: 'I', count: 40, pct: 40 }, { stage: 'II', count: 60, pct: 60 }],
  ecog: [{ ecog: 0, count: 50, pct: 50 }, { ecog: 1, count: 50, pct: 50 }],
  cytogenetics: [
    { marker: 'del(17p)', count: 30, pct: 30, high_risk: true },
    { marker: 'Standard Risk', count: 70, pct: 70, high_risk: false },
  ],
  crab: [
    { label: 'CRAB Met', count: 60, pct: 60 },
    { label: 'CRAB Not Met', count: 40, pct: 40 },
  ],
  bone_lesions: [{ type: 'Lytic', count: 45, pct: 45 }],
  sct_count: 55,
  sct_pct: 55.0,
  refractory_status: [],
}

const flData = {
  ...mmData,
  crab: [],
  bone_lesions: [],
  sct_count: 0,
  sct_pct: 0,
}

describe('StagingPanel — MM disease (isMM=true)', () => {
  it('shows CRAB criteria section', () => {
    render(<StagingPanel data={mmData} isMM={true} />)
    expect(screen.getByText('CRAB Criteria')).toBeInTheDocument()
  })

  it('shows Bone Lesions section when data present', () => {
    render(<StagingPanel data={mmData} isMM={true} />)
    expect(screen.getByText('Bone Lesions')).toBeInTheDocument()
  })

  it('shows Stem Cell Transplant tile with ASCT label', () => {
    render(<StagingPanel data={mmData} isMM={true} />)
    expect(screen.getByText('Received ASCT')).toBeInTheDocument()
    expect(screen.getByText('55.0%')).toBeInTheDocument()
  })

  it('shows ISS Stage Distribution heading', () => {
    render(<StagingPanel data={mmData} isMM={true} />)
    expect(screen.getByText('ISS Stage Distribution')).toBeInTheDocument()
  })
})

describe('StagingPanel — non-MM disease (isMM=false)', () => {
  it('does not render CRAB criteria', () => {
    render(<StagingPanel data={flData} isMM={false} />)
    expect(screen.queryByText('CRAB Criteria')).not.toBeInTheDocument()
  })

  it('does not render Stem Cell Transplant tile', () => {
    render(<StagingPanel data={flData} isMM={false} />)
    expect(screen.queryByText('Received ASCT')).not.toBeInTheDocument()
    expect(screen.queryByText('Stem Cell Transplant')).not.toBeInTheDocument()
  })

  it('shows Disease Stage Distribution heading instead of ISS', () => {
    render(<StagingPanel data={flData} isMM={false} />)
    expect(screen.getByText('Disease Stage Distribution')).toBeInTheDocument()
    expect(screen.queryByText('ISS Stage Distribution')).not.toBeInTheDocument()
  })

  it('still renders ECOG and cytogenetics', () => {
    render(<StagingPanel data={flData} isMM={false} />)
    expect(screen.getByText('ECOG Performance Status')).toBeInTheDocument()
    expect(screen.getByText('Cytogenetic Markers')).toBeInTheDocument()
  })
})

describe('StagingPanel — isMM defaults to false', () => {
  it('hides ASCT tile when isMM prop omitted', () => {
    render(<StagingPanel data={mmData} />)
    expect(screen.queryByText('Received ASCT')).not.toBeInTheDocument()
  })
})

describe('StagingPanel — MM with empty crab/bone', () => {
  it('SCT tile still renders when crab and bone are empty', () => {
    render(<StagingPanel data={{ ...mmData, crab: [], bone_lesions: [] }} isMM={true} />)
    expect(screen.getByText('Received ASCT')).toBeInTheDocument()
  })
})

describe('StagingPanel — no data', () => {
  it('shows empty state when data is undefined', () => {
    render(<StagingPanel data={undefined} />)
    expect(screen.getByText('No data available')).toBeInTheDocument()
  })
})
