import { useState, useRef } from 'react'
import { syncPlayStore, searchPlayStore } from '../../api/reviewApi'
import type { PlayStoreSearchResult } from '../../api/reviewApi'

interface SyncPlayStoreModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function SyncPlayStoreModal({ isOpen, onClose, onSuccess }: SyncPlayStoreModalProps) {
  const [busqueda, setBusqueda] = useState('')
  const [resultados, setResultados] = useState<PlayStoreSearchResult[]>([])
  const [buscando, setBuscando] = useState(false)
  const [seleccionadas, setSeleccionadas] = useState<string[]>([])
  const [cantidadResenas, setCantidadResenas] = useState<number>(20)
  const [loading, setLoading] = useState<boolean>(false)
  const [progreso, setProgreso] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  if (!isOpen) return null

  const handleBuscar = (texto: string) => {
    setBusqueda(texto)
    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (texto.trim().length < 2) {
      setResultados([])
      return
    }

    debounceRef.current = setTimeout(async () => {
      setBuscando(true)
      setError(null)
      try {
        const data = await searchPlayStore(texto.trim(), 'bo', 12)
        setResultados(data.filter((r) => r.app_id))
      } catch (err: any) {
        setError(err.message || 'Error al buscar')
        setResultados([])
      } finally {
        setBuscando(false)
      }
    }, 500)
  }

  const toggleSeleccion = (id: string) => {
    setSeleccionadas((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const seleccionarTodas = () => {
    const idsVisibles = resultados.map((a) => a.app_id)
    const todasMarcadas = idsVisibles.every((id) => seleccionadas.includes(id))
    if (todasMarcadas) {
      setSeleccionadas((prev) => prev.filter((id) => !idsVisibles.includes(id)))
    } else {
      const nuevoSet = new Set([...seleccionadas, ...idsVisibles])
      setSeleccionadas(Array.from(nuevoSet))
    }
  }

  const inferirCategoria = (genre: string | null): string => {
    if (!genre) return 'delivery'
    const g = genre.toLowerCase()
    if (g.includes('food') || g.includes('comida') || g.includes('delivery')) return 'delivery'
    if (g.includes('transport') || g.includes('maps') || g.includes('travel') || g.includes('viaje')) return 'transporte'
    if (g.includes('financ') || g.includes('bank') || g.includes('banca') || g.includes('money')) return 'banca_finanzas'
    if (g.includes('communi') || g.includes('comunica') || g.includes('social') || g.includes('telecom')) return 'telecom'
    return 'delivery'
  }

  const handleSincronizarLote = async () => {
    if (seleccionadas.length === 0) return
    setError(null)
    setLoading(true)

    try {
      for (let i = 0; i < seleccionadas.length; i++) {
        const id = seleccionadas[i]
        const appInfo = resultados.find((a) => a.app_id === id)
        setProgreso(`Sincronizando ${i + 1} de ${seleccionadas.length}: ${appInfo?.title || id}...`)

        await syncPlayStore({
          app_id: id,
          nombre: appInfo?.title,
          categoria: inferirCategoria(appInfo?.genre ?? null),
          pais: 'bo',
          cantidad: cantidadResenas,
        })
      }

      setProgreso('Sincronizacion completada con exito!')
      setTimeout(() => {
        onSuccess()
        onClose()
      }, 1200)
    } catch (err: any) {
      setError(err.message || 'Error durante la sincronizacion por lotes')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(20, 26, 23, 0.65)',
        backdropFilter: 'blur(5px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: '16px',
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--line)',
          borderRadius: '14px',
          width: '100%',
          maxWidth: '780px',
          maxHeight: '88vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px rgba(0,0,0,0.2)',
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div style={{ padding: '24px 28px 16px', borderBottom: '1px solid var(--line)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 700,
                  letterSpacing: '0.6px',
                  color: 'var(--accent)',
                  background: 'var(--accent-soft)',
                  padding: '3px 8px',
                  borderRadius: '4px',
                }}
              >
                PANEL ADMINISTRADOR
              </span>
              <h2 style={{ margin: '6px 0 2px', fontSize: '20px', fontWeight: 700, color: 'var(--ink)' }}>
                Explorador e Ingesta de Google Play Store
              </h2>
              <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                Busca cualquier aplicacion en Google Play Store e importala al ranking con analisis de IA.
              </p>
            </div>
            <button
              type="button"
              onClick={onClose}
              style={{ background: 'none', border: 'none', fontSize: '24px', color: 'var(--muted)', cursor: 'pointer' }}
            >
              &times;
            </button>
          </div>

          {/* Buscador */}
          <div style={{ marginTop: '16px' }}>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                value={busqueda}
                onChange={(e) => handleBuscar(e.target.value)}
                placeholder="Buscar en Google Play Store (ej: pedidosya, uber, banco union, whatsapp)..."
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  borderRadius: '8px',
                  border: '1.5px solid var(--accent)',
                  background: 'var(--canvas)',
                  fontSize: '14px',
                  color: 'var(--ink)',
                  boxSizing: 'border-box',
                }}
              />
              {buscando && (
                <span style={{
                  position: 'absolute',
                  right: '14px',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  fontSize: '12px',
                  color: 'var(--accent)',
                  fontWeight: 600,
                }}>
                  Buscando...
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Barra de accion rapida */}
        <div
          style={{
            padding: '10px 28px',
            background: 'var(--canvas)',
            borderBottom: '1px solid var(--line)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <button
            type="button"
            onClick={seleccionarTodas}
            disabled={resultados.length === 0}
            style={{
              background: 'none',
              border: 'none',
              color: resultados.length > 0 ? 'var(--accent)' : 'var(--muted)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: resultados.length > 0 ? 'pointer' : 'default',
              padding: 0,
            }}
          >
            {resultados.length > 0 && resultados.every((a) => seleccionadas.includes(a.app_id))
              ? 'Desmarcar visibles'
              : 'Seleccionar todas las visibles'}
          </button>

          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
            {resultados.length > 0
              ? `${resultados.length} resultados de Google Play Store`
              : busqueda.length < 2
              ? 'Escribe al menos 2 letras para buscar'
              : 'Sin resultados'}
          </span>
        </div>

        {/* Lista de Aplicaciones (Grid Scrollable) */}
        <div style={{ padding: '20px 28px', overflowY: 'auto', flex: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '14px', minHeight: '200px' }}>
          {resultados.length === 0 && !buscando && busqueda.length >= 2 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px 0', color: 'var(--muted)', fontSize: '13px' }}>
              No se encontraron aplicaciones para "{busqueda}".
            </div>
          )}
          {resultados.length === 0 && !buscando && busqueda.length < 2 && (
            <div style={{ gridColumn: '1 / -1', textAlign: 'center', padding: '40px 0', color: 'var(--muted)', fontSize: '13px' }}>
              Escribe el nombre de cualquier app para buscar en Google Play Store.
            </div>
          )}
          {resultados.map((app) => {
            const isChecked = seleccionadas.includes(app.app_id)
            return (
              <div
                key={app.app_id}
                onClick={() => toggleSeleccion(app.app_id)}
                style={{
                  border: isChecked ? '1.5px solid var(--accent)' : '1px solid var(--line)',
                  background: isChecked ? 'var(--accent-soft)' : 'var(--surface)',
                  borderRadius: '10px',
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  position: 'relative',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                  {app.icon ? (
                    <img
                      src={app.icon}
                      alt={app.title}
                      style={{ width: '40px', height: '40px', borderRadius: '8px', objectFit: 'cover' }}
                    />
                  ) : (
                    <div
                      style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '8px',
                        background: 'var(--accent)',
                        color: '#ffffff',
                        fontWeight: 700,
                        display: 'grid',
                        placeItems: 'center',
                        fontSize: '14px',
                      }}
                    >
                      {(app.title || '?').substring(0, 2).toUpperCase()}
                    </div>
                  )}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: 'var(--ink)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {app.title}
                    </h4>
                    <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                      {app.developer || app.genre || app.app_id}
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}}
                    style={{ accentColor: 'var(--accent)', cursor: 'pointer' }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '11px', color: 'var(--muted)' }}>
                    {app.score != null ? `${app.score.toFixed(1)} / 5.0` : 'Sin rating'}
                  </span>
                  {app.free !== null && (
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: 'var(--canvas)',
                      color: 'var(--muted)',
                      border: '1px solid var(--line)',
                    }}>
                      {app.free ? 'Gratis' : 'De pago'}
                    </span>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Footer con Acciones */}
        <div
          style={{
            padding: '18px 28px',
            borderTop: '1px solid var(--line)',
            background: 'var(--surface)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--ink)' }}>
              {seleccionadas.length} {seleccionadas.length === 1 ? 'app seleccionada' : 'apps seleccionadas'}
            </span>
            {progreso && (
              <span style={{ marginLeft: '12px', fontSize: '12px', color: 'var(--accent)', fontWeight: 600 }}>
                {progreso}
              </span>
            )}
            {error && (
              <span style={{ marginLeft: '12px', fontSize: '12px', color: 'var(--error)' }}>
                {error}
              </span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ fontSize: '12px', color: 'var(--muted)' }}>Opiniones por app:</span>
            <select
              value={cantidadResenas}
              onChange={(e) => setCantidadResenas(Number(e.target.value))}
              style={{ padding: '6px 8px', borderRadius: '6px', border: '1px solid var(--line)', fontSize: '12px' }}
            >
              <option value="10">10 opiniones</option>
              <option value="20">20 opiniones</option>
              <option value="50">50 opiniones</option>
            </select>

            <button
              type="button"
              disabled={seleccionadas.length === 0 || loading}
              onClick={handleSincronizarLote}
              style={{
                padding: '9px 20px',
                borderRadius: '6px',
                background: 'var(--accent)',
                color: '#ffffff',
                border: 'none',
                fontWeight: 600,
                fontSize: '13px',
                cursor: seleccionadas.length === 0 || loading ? 'not-allowed' : 'pointer',
                opacity: seleccionadas.length === 0 || loading ? 0.6 : 1,
              }}
            >
              {loading ? 'Extrayendo en lote...' : `Importar Seleccionadas (${seleccionadas.length})`}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
