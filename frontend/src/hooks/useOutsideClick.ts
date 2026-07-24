import { useEffect, RefObject } from 'react'

/**
 * Calls `handler` when a mousedown event fires outside of `ref`.
 * Only active when `active` is true (avoids attaching the listener when the
 * dropdown / menu is closed).
 */
export function useOutsideClick<T extends HTMLElement>(
  ref: RefObject<T | null>,
  handler: () => void,
  active: boolean,
) {
  useEffect(() => {
    if (!active) return
    function onMouseDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        handler()
      }
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [ref, handler, active])
}
