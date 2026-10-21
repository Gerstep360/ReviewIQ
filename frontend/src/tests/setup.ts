import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

window.scrollTo = vi.fn()
afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.unstubAllGlobals()
  window.location.hash = '/prediccion'
})
