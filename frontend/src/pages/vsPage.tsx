import { useEffect, useState } from 'react'
import { fetchEntities, fetchVersus } from '../api/reviewApi'
import type { Entidad } from '../types/reviewHome'

interface ComparativaDimension {
  dimension: string
  entidad1: { nombre: string; porcentaje: number; color: string }
  entidad2: { nombre: string; porcentaje: number; color: string }
  ganador: string
}

export function VersusPage() {
  const [entidades, setEntidades] = useState<Entidad[]>([])
  const [e1Id, setE1Id] = useState<string>('')
  const [e2Id, setE2Id] = useState<string>('')
  const [comparativa, setComparativa] = useState<Record<string, ComparativaDimension> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchEntities().then((data) => {
      setEntidades(data)
      if (data.length >= 2) {
        setE1Id(data[0].id)
        setE2Id(data[1].id)
      } else if (data.length === 1) {
        setE1Id(data[0].id)
      }
    })
  }, [])

  const ejecutarComparativa = async () => {
    if (!e1Id || !e2Id) return
    if (e1Id === e2Id) {
      setError('Por favor selecciona dos empresas distintas para comparar.')
      return
    }

    setError(null)
    setLoading(true)
    try {
      const data = await fetchVersus(e1Id, e2Id)
      setComparativa(data.comparativa_dimensiones)
    } catch (err: any) {
      setError(err.message || 'Error al obtener la comparativa')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (e1Id && e2Id && e1Id !== e2Id) {
      ejecutarComparativa()
    }
  }, [e1Id, e2Id])

  const ent1 = entidades.find((e) => e.id === e1Id)
  const ent2 = entidades.find((e) => e.id === e2Id)

  const getColorHex = (color: string) => {
    if (color === 'verde') return 'var(--accent)'
    if (color === 'amarillo') return 'var(--gold)'
    return 'var(--error)'
  }

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '10px 0 60px' }}>
      {/* Encabezado */}
      <div style={{ marginBottom: '26px' }}>
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
          ANÁLISIS COMPARATIVO
        </span>
        <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '8px 0 4px', color: 'var(--ink)' }}>
          Comparativa Frente a Frente (Versus)
        </h1>
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--muted)' }}>
          Contrasta el desempeño dimensional entre dos empresas del mercado en base a opiniones públicas.
        </p>
      </div>

      {/* Selectores de Empresas */}
      <div
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--line)',
          borderRadius: '12px',
          padding: '24px',
          marginBottom: '26px',
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '20px', alignItems: 'center' }}>
          {/* Empresa 1 */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--muted)', marginBottom: '6px' }}>
              EMPRESA A:
            </label>
            <select
              value={e1Id}
              onChange={(e) => setE1Id(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--line)',
                background: 'var(--canvas)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--ink)',
              }}
            >
              <option value="">Selecciona una empresa</option>
              {entidades.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre} ({e.categoria})
                </option>
              ))}
            </select>
          </div>

          <div
            style={{
              padding: '8px 14px',
              borderRadius: '20px',
              background: 'var(--canvas)',
              border: '1px solid var(--line)',
              fontWeight: 700,
              fontSize: '12px',
              color: 'var(--muted)',
            }}
          >
            VS
          </div>

          {/* Empresa 2 */}
          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: 'var(--muted)', marginBottom: '6px' }}>
              EMPRESA B:
            </label>
            <select
              value={e2Id}
              onChange={(e) => setE2Id(e.target.value)}
              style={{
                width: '100%',
                padding: '10px 12px',
                borderRadius: '8px',
                border: '1px solid var(--line)',
                background: 'var(--canvas)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--ink)',
              }}
            >
              <option value="">Selecciona una empresa</option>
              {entidades.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.nombre} ({e.categoria})
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div style={{ marginTop: '16px', padding: '10px', background: '#fdf0ef', color: 'var(--error)', borderRadius: '6px', fontSize: '13px', textAlign: 'center' }}>
            {error}
          </div>
        )}
      </div>

      {/* Resultados de la Comparativa */}
      {loading ? (
        <div style={{ padding: '40px', textAlign: 'center', color: 'var(--muted)', fontSize: '14px' }}>
          Analizando dimensiones comparativas con IA...
        </div>
      ) : comparativa && ent1 && ent2 ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Cabecera del Marcador */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '20px',
              background: 'var(--surface)',
              border: '1px solid var(--line)',
              borderRadius: '12px',
              padding: '24px',
            }}
          >
            {/* Lado A */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              {ent1.icono_url && (
                <img src={ent1.icono_url} alt={ent1.nombre} style={{ width: '48px', height: '48px', borderRadius: '10px' }} />
              )}
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--ink)' }}>{ent1.nombre}</h3>
                <span style={{ fontSize: '13px', color: 'var(--gold)', fontWeight: 700, fontFamily: 'var(--mono)' }}>
                  {ent1.calificacion_promedio.toFixed(1)} ★
                </span>
                <span style={{ fontSize: '12px', color: 'var(--muted)', marginLeft: '8px' }}>
                  ({ent1.total_resenas} opiniones)
                </span>
              </div>
            </div>

            {/* Lado B */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', justifyContent: 'flex-end', textAlign: 'right' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: 'var(--ink)' }}>{ent2.nombre}</h3>
                <span style={{ fontSize: '12px', color: 'var(--muted)', marginRight: '8px' }}>
                  ({ent2.total_resenas} opiniones)
                </span>
                <span style={{ fontSize: '13px', color: 'var(--gold)', fontWeight: 700, fontFamily: 'var(--mono)' }}>
                  {ent2.calificacion_promedio.toFixed(1)} ★
                </span>
              </div>
              {ent2.icono_url && (
                <img src={ent2.icono_url} alt={ent2.nombre} style={{ width: '48px', height: '48px', borderRadius: '10px' }} />
              )}
            </div>
          </div>

          {/* Duelo de las 5 Dimensiones */}
          <div
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--line)',
              borderRadius: '12px',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
            }}
          >
            <h3 style={{ margin: '0 0 8px', fontSize: '16px', fontWeight: 700, color: 'var(--ink)' }}>
              Comparación por Dimensión de Servicio
            </h3>

            {Object.entries(comparativa).map(([key, item]) => (
              <div
                key={key}
                style={{
                  padding: '16px 20px',
                  borderRadius: '10px',
                  border: '1px solid var(--line)',
                  background: 'var(--canvas)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <span style={{ fontWeight: 700, fontSize: '14px', color: 'var(--ink)' }}>
                    {item.dimension}
                  </span>
                  <span
                    style={{
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '3px 10px',
                      borderRadius: '4px',
                      background: item.ganador === 'Empate' ? '#e9ece5' : 'var(--accent-soft)',
                      color: item.ganador === 'Empate' ? 'var(--muted)' : 'var(--accent)',
                    }}
                  >
                    {item.ganador === 'Empate' ? 'EMPATE TÉCNICO' : `VENTAJA: ${item.ganador.toUpperCase()}`}
                  </span>
                </div>

                {/* Barras Frente a Frente */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                  {/* Barra Entidad 1 */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--muted)' }}>{item.entidad1.nombre}</span>
                      <span style={{ fontWeight: 700, fontFamily: 'var(--mono)', color: getColorHex(item.entidad1.color) }}>
                        {item.entidad1.porcentaje.toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ height: '7px', background: '#e0e5dc', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${item.entidad1.porcentaje}%`,
                          background: getColorHex(item.entidad1.color),
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>

                  {/* Barra Entidad 2 */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--muted)' }}>{item.entidad2.nombre}</span>
                      <span style={{ fontWeight: 700, fontFamily: 'var(--mono)', color: getColorHex(item.entidad2.color) }}>
                        {item.entidad2.porcentaje.toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ height: '7px', background: '#e0e5dc', borderRadius: '4px', overflow: 'hidden' }}>
                      <div
                        style={{
                          height: '100%',
                          width: `${item.entidad2.porcentaje}%`,
                          background: getColorHex(item.entidad2.color),
                          borderRadius: '4px',
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ padding: '60px', textAlign: 'center', background: 'var(--surface)', borderRadius: '12px', border: '1px solid var(--line)', color: 'var(--muted)', fontSize: '13px' }}>
          Selecciona dos empresas para generar la comparativa dimensional.
        </div>
      )}
    </div>
  )
}
