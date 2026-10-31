import type { SemaforoMap, DimensionSemaforo } from '../../types/reviewHome'

interface SemaforoBarsProps {
  semaforo: SemaforoMap
}

export function SemaforoBars({ semaforo }: SemaforoBarsProps) {
  const items: { key: keyof SemaforoMap; data: DimensionSemaforo }[] = [
    { key: 'atencion_cliente', data: semaforo.atencion_cliente },
    { key: 'envio_logistica', data: semaforo.envio_logistica },
    { key: 'calidad_producto', data: semaforo.calidad_producto },
    { key: 'precio_valor', data: semaforo.precio_valor },
    { key: 'ux_bugs', data: semaforo.ux_bugs },
  ]

  const getBadgeStyle = (color: 'verde' | 'amarillo' | 'rojo') => {
    switch (color) {
      case 'verde':
        return {
          label: 'ÓPTIMO',
          textColor: 'var(--accent)',
          bgColor: 'var(--accent-soft)',
          barColor: 'var(--accent)',
        }
      case 'amarillo':
        return {
          label: 'ATENCIÓN',
          textColor: 'var(--gold)',
          bgColor: '#fef7ea',
          barColor: 'var(--gold)',
        }
      case 'rojo':
        return {
          label: 'CRÍTICO',
          textColor: 'var(--error)',
          bgColor: '#fdf0ef',
          barColor: 'var(--error)',
        }
    }
  }

  const itemsActivos = items.filter(({ data }) => data && data.menciones > 0)

  if (itemsActivos.length === 0) {
    return (
      <div
        style={{
          padding: '24px',
          textAlign: 'center',
          color: 'var(--muted)',
          fontSize: '13px',
          background: 'var(--canvas)',
          borderRadius: '8px',
          border: '1px dashed var(--line)',
        }}
      >
        Aún no hay suficientes opiniones que mencionen dimensiones específicas para esta app.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {itemsActivos.map(({ key, data }) => {
        const badge = getBadgeStyle(data.color)

        return (
          <div
            key={key}
            style={{
              background: 'var(--surface)',
              border: '1px solid var(--line)',
              borderRadius: '8px',
              padding: '14px 18px',
            }}
          >
            {/* Cabecera de la dimensión */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '10px',
              }}
            >
              <div>
                <span style={{ fontWeight: 600, fontSize: '14px', color: 'var(--ink)' }}>
                  {data.etiqueta}
                </span>
                <span
                  style={{
                    marginLeft: '10px',
                    fontSize: '12px',
                    color: 'var(--muted)',
                  }}
                >
                  ({data.menciones} menciones analizadas)
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    letterSpacing: '0.5px',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    color: badge.textColor,
                    background: badge.bgColor,
                    border: `1px solid ${badge.textColor}22`,
                  }}
                >
                  {badge.label}
                </span>
                <span
                  style={{
                    fontFamily: 'var(--mono)',
                    fontSize: '15px',
                    fontWeight: 700,
                    color: badge.textColor,
                    minWidth: '54px',
                    textAlign: 'right',
                  }}
                >
                  {data.porcentaje.toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Pista de la barra de progreso */}
            <div
              style={{
                height: '8px',
                width: '100%',
                background: '#e9ece5',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(Math.max(data.porcentaje, 0), 100)}%`,
                  background: badge.barColor,
                  borderRadius: '4px',
                  transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)',
                }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}