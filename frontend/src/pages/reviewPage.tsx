import { useEffect, useState } from 'react'
import {
  fetchEntities,
  fetchDiagnostic,
  fetchReviews,
  deleteEntityApi,
} from '../api/reviewApi'
import type {
  Entidad,
  SemaforoMap,
  Resena,
  UserSession,
} from '../types/reviewHome'
import { SemaforoBars } from '../components/reviewComponents/SemaforoBars'
import { SyncPlayStoreModal } from '../components/reviewComponents/SyncPlayStoreModal'
import { ReviewFormModal } from '../components/reviewComponents/ReviewFormModal'
import { AuthModal } from '../components/reviewComponents/AuthModal'

const CATEGORIA_LABELS: Record<string, string> = {
  todas: 'Todas',
  delivery: 'Delivery',
  transporte: 'Transporte',
  banca_finanzas: 'Banca y Finanzas',
  telecom: 'Telecomunicaciones',
  compras: 'Compras',
  juegos: 'Juegos',
}

interface ReputationPageProps {
  user: UserSession | null
  onAuthSuccess: (user: UserSession) => void
}

export function ReputationPage({ user, onAuthSuccess }: ReputationPageProps) {
  const [entidades, setEntidades] = useState<Entidad[]>([])
  const [entidadSeleccionada, setEntidadSeleccionada] = useState<Entidad | null>(null)
  const [semaforo, setSemaforo] = useState<SemaforoMap | null>(null)
  const [, setDistribucion] = useState<Record<string, number>>({})
  const [resenas, setResenas] = useState<Resena[]>([])
  const [filtroEstrellas, setFiltroEstrellas] = useState<number | undefined>(undefined)

  const [busqueda, setBusqueda] = useState('')
  const [categoriaFiltro, setCategoriaFiltro] = useState<string>('todas')
  const [loading, setLoading] = useState(true)

  // Modales
  const [modalSyncOpen, setModalSyncOpen] = useState(false)
  const [modalReviewOpen, setModalReviewOpen] = useState(false)
  const [modalAuthOpen, setModalAuthOpen] = useState(false)

  // Cargar lista de entidades
  const cargarEntidades = async () => {
    try {
      setLoading(true)
      const data = await fetchEntities()
      setEntidades(data)
      if (data.length > 0 && !entidadSeleccionada) {
        seleccionarEntidad(data[0])
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Cargar diagnóstico y semáforo de la entidad elegida
  const seleccionarEntidad = async (ent: Entidad) => {
    setEntidadSeleccionada(ent)
    try {
      const diag = await fetchDiagnostic(ent.id)
      setSemaforo(diag.semaforo)
      setDistribucion(diag.distribucion_estrellas_ia)
      cargarResenas(ent.id, filtroEstrellas)
    } catch (err) {
      console.error(err)
    }
  }

  // Cargar reseñas filtradas
  const cargarResenas = async (entId: string, estrellas?: number) => {
    try {
      const data = await fetchReviews(entId, { estrellas })
      setResenas(data)
    } catch (err) {
      console.error(err)
    }
  }

  const handleEliminarEntidad = async (e: React.MouseEvent, entId: string) => {
    e.stopPropagation()
    if (!confirm('¿Estás seguro de que deseas eliminar esta empresa y sus análisis?')) return
    try {
      await deleteEntityApi(entId)
      if (entidadSeleccionada?.id === entId) {
        setEntidadSeleccionada(null)
        setSemaforo(null)
      }
      cargarEntidades()
    } catch (err) {
      alert('Error al eliminar')
    }
  }

  const handleAbrirReview = () => {
    if (!user) {
      setModalAuthOpen(true)
    } else {
      setModalReviewOpen(true)
    }
  }

  useEffect(() => {
    cargarEntidades()
  }, [])

  useEffect(() => {
    if (entidadSeleccionada) {
      cargarResenas(entidadSeleccionada.id, filtroEstrellas)
    }
  }, [filtroEstrellas])

  // Filtrado de tarjetas
  const entidadesFiltradas = entidades.filter((ent) => {
    const coincideTexto =
      ent.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      ent.categoria.toLowerCase().includes(busqueda.toLowerCase())
    const coincideCat = categoriaFiltro === 'todas' || ent.categoria === categoriaFiltro
    return coincideTexto && coincideCat
  })

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '10px 0 60px' }}>
      {/* Encabezado Principal */}
      <div style={{ marginBottom: '28px' }}>
        <span
          style={{
            fontSize: '11px',
            fontWeight: 700,
            letterSpacing: '0.8px',
            color: 'var(--accent)',
            background: 'var(--accent-soft)',
            padding: '4px 10px',
            borderRadius: '4px',
          }}
        >
          DECISIONES INTELIGENTES
        </span>
        <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '8px 0 4px', color: 'var(--ink)' }}>
          Encuentra la app con mejor atención y servicio
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--muted)' }}>
          Mira cómo califican los clientes el envío, la atención y los precios antes de hacer tu pedido o viaje.
        </p>
      </div>

      {/* Barra de Búsqueda, Filtros y Acción de Administrador */}
      <div
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--line)',
          borderRadius: '10px',
          padding: '16px 20px',
          marginBottom: '26px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
        }}
      >
        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '240px' }}>
            <input
              type="text"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Buscar en el catálogo por nombre..."
              style={{
                width: '100%',
                padding: '9px 12px',
                borderRadius: '6px',
                border: '1px solid var(--line)',
                background: 'var(--canvas)',
                fontSize: '13px',
                color: 'var(--ink)',
                boxSizing: 'border-box',
              }}
            />
          </div>

          {/* Botón Administrador para Ingesta */}
          {user?.role === 'admin' && (
            <button
              type="button"
              onClick={() => setModalSyncOpen(true)}
              style={{
                padding: '9px 18px',
                borderRadius: '6px',
                background: 'var(--accent)',
                color: '#ffffff',
                border: 'none',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              + Importar Apps de Play Store
            </button>
          )}
        </div>

        {/* Chips de Categorías */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {[
            { id: 'todas', label: 'Todas' },
            { id: 'delivery', label: 'Delivery' },
            { id: 'transporte', label: 'Transporte' },
            { id: 'banca_finanzas', label: 'Banca y Finanzas' },
            { id: 'telecom', label: 'Telecomunicaciones' },
            { id: 'compras', label: 'Compras' },
            { id: 'juegos', label: 'Juegos' },
          ].map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setCategoriaFiltro(cat.id)}
              style={{
                fontSize: '12px',
                padding: '5px 12px',
                borderRadius: '16px',
                border: categoriaFiltro === cat.id ? '1.5px solid var(--accent)' : '1px solid var(--line)',
                background: categoriaFiltro === cat.id ? 'var(--accent-soft)' : 'var(--canvas)',
                color: categoriaFiltro === cat.id ? 'var(--accent)' : 'var(--ink)',
                fontWeight: categoriaFiltro === cat.id ? 700 : 500,
                cursor: 'pointer',
              }}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grilla: Catálogo de Empresas a la Izquierda y Detalle de Diagnóstico a la Derecha */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: '24px', alignItems: 'start' }}>
        {/* ================= COLUMNA IZQUIERDA: RANKING DE TARJETAS ================= */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--ink)' }}>
              Ranking de Empresas ({entidadesFiltradas.length})
            </h3>
          </div>

          {loading ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--muted)', fontSize: '13px' }}>
              Cargando directorio de empresas...
            </div>
          ) : entidadesFiltradas.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', background: 'var(--surface)', borderRadius: '8px', border: '1px solid var(--line)', color: 'var(--muted)', fontSize: '13px' }}>
              No se encontraron empresas con ese criterio.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {entidadesFiltradas.map((ent) => {
                const isSelected = entidadSeleccionada?.id === ent.id
                return (
                  <div
                    key={ent.id}
                    onClick={() => seleccionarEntidad(ent)}
                    style={{
                      background: isSelected ? 'var(--accent-soft)' : 'var(--surface)',
                      border: isSelected ? '2px solid var(--accent)' : '1px solid var(--line)',
                      borderRadius: '10px',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                      position: 'relative',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      {/* Logo oficial o monograma fallback */}
                      {ent.icono_url ? (
                        <img
                          src={ent.icono_url}
                          alt={ent.nombre}
                          style={{ width: '44px', height: '44px', borderRadius: '10px', objectFit: 'cover' }}
                        />
                      ) : (
                        <div
                          style={{
                            width: '44px',
                            height: '44px',
                            borderRadius: '10px',
                            background: 'var(--accent)',
                            color: '#ffffff',
                            fontWeight: 700,
                            display: 'grid',
                            placeItems: 'center',
                            fontSize: '16px',
                          }}
                        >
                          {ent.nombre.substring(0, 2).toUpperCase()}
                        </div>
                      )}

                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--ink)' }}>
                            {ent.nombre}
                          </h4>
                          <span
                            style={{
                              fontSize: '11px',
                              padding: '2px 7px',
                              borderRadius: '4px',
                              background: 'var(--canvas)',
                              color: 'var(--muted)',
                              border: '1px solid var(--line)',
                              textTransform: 'capitalize',
                            }}
                          >
                            {CATEGORIA_LABELS[ent.categoria] || ent.categoria.replace('_', ' ')}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '6px' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--gold)', fontFamily: 'var(--mono)' }}>
                            {ent.calificacion_promedio.toFixed(1)} / 5.0
                          </span>
                          <span style={{ fontSize: '12px', color: 'var(--muted)' }}>
                            {ent.total_resenas} opiniones analizadas
                          </span>
                        </div>
                      </div>

                      {/* Botón eliminar (Solo Admin) */}
                      {user?.role === 'admin' && (
                        <button
                          type="button"
                          onClick={(e) => handleEliminarEntidad(e, ent.id)}
                          title="Eliminar entidad"
                          style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--error)',
                            fontSize: '14px',
                            cursor: 'pointer',
                            padding: '6px',
                            borderRadius: '4px',
                          }}
                        >
                          Eliminar
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* ================= COLUMNA DERECHA: DIAGNÓSTICO Y SEMÁFORO ================= */}
        <div>
          {entidadSeleccionada ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Tarjeta de Resumen de la Entidad */}
              <div
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: '12px',
                  padding: '20px 24px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                    {entidadSeleccionada.icono_url && (
                      <img
                        src={entidadSeleccionada.icono_url}
                        alt={entidadSeleccionada.nombre}
                        style={{ width: '52px', height: '52px', borderRadius: '12px' }}
                      />
                    )}
                    <div>
                      <h2 style={{ margin: '0 0 4px', fontSize: '20px', fontWeight: 700, color: 'var(--ink)' }}>
                        {entidadSeleccionada.nombre}
                      </h2>
                      <span style={{ fontSize: '12px', color: 'var(--muted)', fontFamily: 'var(--mono)' }}>
                        App en Google Play Store · Bolivia
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={handleAbrirReview}
                    style={{
                      padding: '8px 16px',
                      borderRadius: '6px',
                      background: 'var(--accent)',
                      color: '#ffffff',
                      border: 'none',
                      fontSize: '13px',
                      fontWeight: 600,
                      cursor: 'pointer',
                    }}
                  >
                    Dejar mi opinión
                  </button>
                </div>
              </div>

              {/* Semáforo de Experiencia (Las 5 dimensiones) */}
              <div
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: '12px',
                  padding: '22px 24px',
                }}
              >
                <div style={{ marginBottom: '18px' }}>
                  <h3 style={{ margin: '0 0 4px', fontSize: '16px', fontWeight: 700, color: 'var(--ink)' }}>
                    ¿Cómo rinde esta app? (Semáforo de Calidad)
                  </h3>
                  <p style={{ margin: 0, fontSize: '13px', color: 'var(--muted)' }}>
                    Calificación calculada por la IA según lo que dicen los usuarios:
                  </p>
                </div>

                {semaforo ? (
                  <SemaforoBars semaforo={semaforo} />
                ) : (
                  <div style={{ padding: '20px', textAlign: 'center', color: 'var(--muted)', fontSize: '13px' }}>
                    Calculando semáforo...
                  </div>
                )}
              </div>

              {/* Muro de Reseñas */}
              <div
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--line)',
                  borderRadius: '12px',
                  padding: '22px 24px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--ink)' }}>
                    Comentarios de los usuarios ({resenas.length})
                  </h3>

                  {/* Filtro por estrellas */}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      type="button"
                      onClick={() => setFiltroEstrellas(undefined)}
                      style={{
                        padding: '4px 10px',
                        fontSize: '11px',
                        fontWeight: 600,
                        borderRadius: '4px',
                        border: '1px solid var(--line)',
                        background: filtroEstrellas === undefined ? 'var(--accent)' : 'var(--canvas)',
                        color: filtroEstrellas === undefined ? '#ffffff' : 'var(--ink)',
                        cursor: 'pointer',
                      }}
                    >
                      Todas
                    </button>
                    {[5, 4, 3, 2, 1].map((val) => (
                      <button
                        key={val}
                        type="button"
                        onClick={() => setFiltroEstrellas(val)}
                        style={{
                          padding: '4px 8px',
                          fontSize: '11px',
                          fontWeight: 600,
                          borderRadius: '4px',
                          border: '1px solid var(--line)',
                          background: filtroEstrellas === val ? 'var(--accent)' : 'var(--canvas)',
                          color: filtroEstrellas === val ? '#ffffff' : 'var(--ink)',
                          cursor: 'pointer',
                        }}
                      >
                        {val}★
                      </button>
                    ))}
                  </div>
                </div>

                {resenas.length === 0 ? (
                  <div style={{ padding: '20px', textAlign: 'center', color: 'var(--muted)', fontSize: '13px' }}>
                    No hay opiniones con este filtro.
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '420px', overflowY: 'auto' }}>
                    {resenas.map((r) => (
                      <div
                        key={r.id}
                        style={{
                          padding: '14px',
                          borderRadius: '8px',
                          border: '1px solid var(--line)',
                          background: 'var(--canvas)',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                          <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--gold)', fontFamily: 'var(--mono)' }}>
                            {r.diagnostico ? `${r.diagnostico.estrellas_predichas}★ (IA)` : `${r.estrellas_origen}★`}
                          </span>

                          {r.diagnostico && (
                            <span
                              style={{
                                fontSize: '11px',
                                fontWeight: 700,
                                textTransform: 'uppercase',
                                color:
                                  r.diagnostico.sentimiento_global === 'positivo'
                                    ? 'var(--accent)'
                                    : r.diagnostico.sentimiento_global === 'negativo'
                                    ? 'var(--error)'
                                    : 'var(--gold)',
                              }}
                            >
                              Sentimiento {r.diagnostico.sentimiento_global}
                            </span>
                          )}
                        </div>

                        <p style={{ margin: 0, fontSize: '13px', color: 'var(--ink)', lineHeight: 1.5 }}>
                          "{r.texto}"
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ padding: '60px', textAlign: 'center', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--line)', color: 'var(--muted)' }}>
              Selecciona una empresa del ranking para visualizar su semáforo.
            </div>
          )}
        </div>
      </div>

      {/* Modales */}
      <SyncPlayStoreModal
        isOpen={modalSyncOpen}
        onClose={() => setModalSyncOpen(false)}
        onSuccess={cargarEntidades}
      />

      {entidadSeleccionada && (
        <ReviewFormModal
          isOpen={modalReviewOpen}
          onClose={() => setModalReviewOpen(false)}
          entidadId={entidadSeleccionada.id}
          entidadNombre={entidadSeleccionada.nombre}
          onSuccess={(nuevoSemaforo) => {
            setSemaforo(nuevoSemaforo)
            cargarEntidades()
            cargarResenas(entidadSeleccionada.id)
          }}
        />
      )}

      <AuthModal
        isOpen={modalAuthOpen}
        onClose={() => setModalAuthOpen(false)}
        onSuccess={onAuthSuccess}
      />
    </div>
  )
}