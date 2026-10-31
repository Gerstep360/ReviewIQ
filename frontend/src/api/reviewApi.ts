import type {
  Entidad,
  SemaforoMap,
  Resena,
  UserSession,
} from '../types/reviewHome'

const BASE_URL = '/api/v1/reputation'

export async function fetchEntities(categoria?: string): Promise<Entidad[]> {
  const url = categoria ? `${BASE_URL}/entities/?categoria=${categoria}` : `${BASE_URL}/entities/`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Error al cargar la lista de entidades')
  const json = await res.json()
  return json.data || []
}

export async function fetchDiagnostic(entityId: string): Promise<{
  entidad: Entidad
  distribucion_estrellas_ia: Record<string, number>
  semaforo: SemaforoMap
}> {
  const res = await fetch(`${BASE_URL}/entities/${entityId}/diagnostic/`)
  if (!res.ok) throw new Error('Error al obtener el diagnóstico de la entidad')
  return res.json()
}

export async function fetchReviews(
  entityId: string,
  filtros?: { estrellas?: number; sentimiento?: string; dimension?: string }
): Promise<Resena[]> {
  const params = new URLSearchParams()
  if (filtros?.estrellas) params.set('estrellas', String(filtros.estrellas))
  if (filtros?.sentimiento) params.set('sentimiento', filtros.sentimiento)
  if (filtros?.dimension) params.set('dimension', filtros.dimension)

  const url = `${BASE_URL}/entities/${entityId}/reviews/?${params.toString()}`
  const res = await fetch(url)
  if (!res.ok) throw new Error('Error al cargar las reseñas')
  const json = await res.json()
  return json.reviews || []
}

export async function postUserReview(
  entityId: string,
  texto: string,
  estrellas: number
): Promise<{ comentario: Resena; semaforo_actualizado: SemaforoMap }> {
  const res = await fetch(`${BASE_URL}/entities/${entityId}/reviews/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto, estrellas }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.message || 'Error al enviar la reseña')
  }
  return res.json()
}

export async function fetchVersus(e1: string, e2: string) {
  const res = await fetch(`${BASE_URL}/versus/?e1=${e1}&e2=${e2}`)
  if (!res.ok) throw new Error('Error al obtener la comparativa')
  return res.json()
}

export async function syncPlayStore(payload: {
  app_id: string
  nombre?: string
  categoria?: string
  cantidad?: number
  pais?: string
}) {
  const res = await fetch(`${BASE_URL}/sync/playstore/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.message || 'Error al sincronizar con Play Store')
  }
  return res.json()
}

export interface PlayStoreSearchResult {
  app_id: string
  title: string
  score: number | null
  icon: string | null
  developer: string | null
  genre: string | null
  free: boolean | null
  description: string
  installs: string | null
}

export async function searchPlayStore(query: string, country = 'bo', n = 10): Promise<PlayStoreSearchResult[]> {
  const params = new URLSearchParams({ q: query, country, n: String(n) })
  const res = await fetch(`${BASE_URL}/search/playstore/?${params.toString()}`)
  if (!res.ok) throw new Error('Error al buscar en Play Store')
  const json = await res.json()
  return json.results || []
}

export async function deleteEntityApi(entityId: string) {
  const res = await fetch(`${BASE_URL}/entities/${entityId}/`, {
    method: 'DELETE',
  })
  if (!res.ok) throw new Error('Error al eliminar la entidad')
  return res.json()
}

export async function loginApi(username: string, password: string): Promise<UserSession> {
  const res = await fetch(`${BASE_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.message || 'Credenciales incorrectas')
  }
  const data = await res.json()
  return data.user
}

export async function registerApi(username: string, password: string, nombre?: string): Promise<UserSession> {
  const res = await fetch(`${BASE_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, nombre }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.message || 'Error al registrar usuario')
  }
  const data = await res.json()
  return data.user
}