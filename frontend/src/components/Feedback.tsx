import type { ApiError } from '../api/client'
import type { ReactNode } from 'react'
import { Icon } from './Icon'

export function ErrorNotice({
  error,
  retry,
  title = 'No se pudo completar la consulta',
}: {
  error: ApiError
  retry: () => void
  title?: string
}) {
  return (
    <div className="error-notice" role="alert">
      <h3>{title}</h3>
      <p>{error.message}</p>
      <button type="button" className="button secondary" onClick={retry}>
        <Icon name="refresh" />
        Reintentar
      </button>
    </div>
  )
}

export function Loading({ children }: { children: ReactNode }) {
  return (
    <div className="loading-state" role="status">
      <span className="spinner" aria-hidden="true" />
      <p>{children}</p>
    </div>
  )
}
