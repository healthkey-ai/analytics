/**
 * Merge multiple Kaplan-Meier curves onto a shared time axis for Recharts.
 *
 * Each input curve is identified by `key`. The output is an array of flat
 * objects `{ time, [key]: survival, ... }` covering every distinct time point
 * across all curves, with step-function forward-fill for curves that have no
 * event at a given time.
 */
export function mergeKMCurves(
  curves: { key: string; curve: { time: number; survival: number }[] }[]
): Record<string, number>[] {
  const allTimes = [
    ...new Set(curves.flatMap((c) => c.curve.map((p) => p.time))),
  ].sort((a, b) => a - b)

  return allTimes.map((time) => {
    const point: Record<string, number> = { time }
    curves.forEach(({ key, curve }) => {
      const last = [...curve].reverse().find((p) => p.time <= time)
      point[key]  = last ? last.survival : 1.0
    })
    return point
  })
}
