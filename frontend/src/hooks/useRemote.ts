import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'

const asError = (error: unknown) =>
  error instanceof ApiError
    ? error
    : new ApiError('No se pudo completar la solicitud. Vuelve a intentarlo.')

export function useRemote<T>(fetcher: (signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [pending, setPending] = useState(true)
  const current = useRef<AbortController | null>(null)
  const execute = useCallback(async () => {
    current.current?.abort()
    const controller = new AbortController()
    current.current = controller
    try {
      const value = await fetcher(controller.signal)
      if (!controller.signal.aborted) {
        setData(value)
        return value
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        setData(null)
        setError(asError(error))
      }
    } finally {
      if (!controller.signal.aborted) setPending(false)
    }
    return null
  }, [fetcher])
  const reload = useCallback(() => {
    setPending(true)
    setError(null)
    return execute()
  }, [execute])
  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect -- Estado actualizado tras resolver la petición externa, no de forma síncrona.
    void execute()
    return () => current.current?.abort()
  }, [execute])
  return { data, error, pending, reload }
}

export function useAnalysis<T>(fetcher: (text: string, signal: AbortSignal) => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [pending, setPending] = useState(false)
  const current = useRef<AbortController | null>(null)
  const reset = useCallback(() => {
    current.current?.abort()
    setData(null)
    setError(null)
    setPending(false)
  }, [])
  const run = useCallback(
    async (text: string) => {
      current.current?.abort()
      const controller = new AbortController()
      current.current = controller
      setPending(true)
      setError(null)
      setData(null)
      try {
        const value = await fetcher(text, controller.signal)
        if (!controller.signal.aborted) {
          setData(value)
          return value
        }
      } catch (error) {
        if (!controller.signal.aborted) setError(asError(error))
      } finally {
        if (!controller.signal.aborted) setPending(false)
      }
      return null
    },
    [fetcher],
  )
  useEffect(() => () => current.current?.abort(), [])
  return { data, error, pending, reset, run }
}
