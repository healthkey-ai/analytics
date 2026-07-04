import { describe, it, expect } from 'vitest'
import { mergeKMCurves } from '../kmChartUtils'

describe('mergeKMCurves', () => {
  it('returns an empty array when given no curves', () => {
    expect(mergeKMCurves([])).toEqual([])
  })

  it('handles a single curve with no CI fields', () => {
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 6, survival: 0.8 },
          { time: 12, survival: 0.6 },
        ],
      },
    ])

    expect(result).toHaveLength(3)
    expect(result[0]).toEqual({ time: 0, g0: 1.0 })
    expect(result[1]).toEqual({ time: 6, g0: 0.8 })
    expect(result[2]).toEqual({ time: 12, g0: 0.6 })
  })

  it('merges two curves onto a shared time axis with correct keys', () => {
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 6, survival: 0.7 },
        ],
      },
      {
        key: 'g1',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 6, survival: 0.5 },
        ],
      },
    ])

    expect(result).toHaveLength(2)
    expect(result[0]).toEqual({ time: 0, g0: 1.0, g1: 1.0 })
    expect(result[1]).toEqual({ time: 6, g0: 0.7, g1: 0.5 })
  })

  it('uses step-function forward-fill for curves with different time points', () => {
    // g0 has an event at time 3; g1 does not — g1 should carry its last value
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 3, survival: 0.8 },
          { time: 9, survival: 0.6 },
        ],
      },
      {
        key: 'g1',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 9, survival: 0.5 },
        ],
      },
    ])

    // Union of times: 0, 3, 9
    expect(result).toHaveLength(3)

    // time=0: both curves start at 1.0
    expect(result[0]).toMatchObject({ time: 0, g0: 1.0, g1: 1.0 })

    // time=3: g0 drops; g1 has no point at 3, so it forward-fills from time=0 → 1.0
    expect(result[1]).toMatchObject({ time: 3, g0: 0.8, g1: 1.0 })

    // time=9: both curves have an event
    expect(result[2]).toMatchObject({ time: 9, g0: 0.6, g1: 0.5 })
  })

  it('emits CI keys only when source points carry ci_lower / ci_upper', () => {
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0, ci_lower: 1.0, ci_upper: 1.0 },
          { time: 6, survival: 0.8, ci_lower: 0.65, ci_upper: 0.9 },
        ],
      },
    ])

    expect(result[1]).toMatchObject({
      time: 6,
      g0: 0.8,
      g0_lower: 0.65,
      g0_upper: 0.9,
    })
  })

  it('does not emit CI keys for curves without CI data', () => {
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 6, survival: 0.8 },
        ],
      },
    ])

    expect(result[1]).not.toHaveProperty('g0_lower')
    expect(result[1]).not.toHaveProperty('g0_upper')
  })

  it('returns time points sorted in ascending order', () => {
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 12, survival: 0.5 },
          { time: 0, survival: 1.0 },
          { time: 6, survival: 0.75 },
        ],
      },
    ])

    const times = result.map(p => p.time)
    expect(times).toEqual([0, 6, 12])
  })

  it('uses the last curve value before or at the requested time (step-function)', () => {
    // At time=5, the most recent point at or before 5 for g0 is time=3 (survival=0.9)
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 3, survival: 0.9 },
          { time: 8, survival: 0.7 },
        ],
      },
      {
        key: 'g1',
        curve: [
          { time: 0, survival: 1.0 },
          { time: 5, survival: 0.85 },
        ],
      },
    ])

    // Union: 0, 3, 5, 8
    const at5 = result.find(p => p.time === 5)
    expect(at5).toBeDefined()
    // g0 at time=5 should forward-fill from time=3 → 0.9
    expect(at5!.g0).toBe(0.9)
    expect(at5!.g1).toBe(0.85)
  })

  it('defaults to survival 1.0 for a curve with no points at or before the requested time', () => {
    // g1 only has a point at time=10; at time=0 there is nothing before it → default 1.0
    const result = mergeKMCurves([
      {
        key: 'g0',
        curve: [{ time: 0, survival: 1.0 }],
      },
      {
        key: 'g1',
        curve: [{ time: 10, survival: 0.6 }],
      },
    ])

    const at0 = result.find(p => p.time === 0)
    expect(at0).toBeDefined()
    expect(at0!.g1).toBe(1.0)
  })
})
