import { useState } from 'react'
import { postUserReview } from '../../api/reviewApi'
import type { SemaforoMap } from '../../types/reviewHome'

interface ReviewFormModalProps {
  isOpen: boolean
  onClose: () => void
  entidadId: string
  entidadNombre: string
  onSuccess: (updatedSemaforo: SemaforoMap) => void
}

export function ReviewFormModal({
  isOpen,
  onClose,
  entidadId,
  entidadNombre,
  onSuccess,
}: ReviewFormModalProps) {
  const [texto, setTexto] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resultadoIa, setResultadoIa] = useState<{
    estrellas_predichas: number
    confianza: number
    sentimiento: string
  } | null>(null)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (texto.trim().length < 5) {
      setError('Por favor escribe al menos 5 caracteres en tu opinión.')
      return
    }

    setError(null)
    setLoading(true)

    try {
      // El modelo de IA inferirá las estrellas automáticamente a partir del texto
      const res = await postUserReview(entidadId, texto, 5)
      const diag = res.comentario.diagnostico
      if (diag) {
        setResultadoIa({
          estrellas_predichas: diag.estrellas_predichas,
          confianza: Math.round(diag.probabilidad_mayor * 100),
          sentimiento: diag.sentimiento_global,
        })
      }

      setTimeout(() => {
        onSuccess(res.semaforo_actualizado)
        onClose()
      }, 2200)
    } catch (err: any) {
      setError(err.message || 'Error al procesar tu opinión con el modelo')
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
        backdropFilter: 'blur(4px)',
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
          borderRadius: '12px',
          width: '100%',
          maxWidth: '520px',
          padding: '28px',
          boxShadow: '0 20px 40px rgba(0,0,0,0.15)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
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
              INFERENCIA AUTOMÁTICA
            </span>
            <h3 style={{ margin: '6px 0 0', fontSize: '18px', fontWeight: 700, color: 'var(--ink)' }}>
              Evaluar {entidadNombre}
            </h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: '22px', color: 'var(--muted)', cursor: 'pointer' }}
          >
            &times;
          </button>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--muted)', margin: '0 0 16px', lineHeight: 1.5 }}>
          Escribe tu opinión natural. El modelo de Machine Learning de ReviewIQ analizará el texto para predecir la calificación de estrellas y actualizar el semáforo automáticamente.
        </p>

        {error && (
          <div style={{ padding: '10px', background: '#fdf0ef', color: 'var(--error)', borderRadius: '6px', fontSize: '13px', marginBottom: '14px' }}>
            {error}
          </div>
        )}

        {/* Tarjeta de resultado cuando la IA termina la inferencia */}
        {resultadoIa && (
          <div
            style={{
              padding: '14px',
              background: 'var(--accent-soft)',
              color: 'var(--ink)',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '16px',
              border: '1px solid var(--accent)44',
            }}
          >
            <div style={{ fontWeight: 700, color: 'var(--accent)', marginBottom: '4px' }}>
              Diagnóstico de Inteligencia Artificial:
            </div>
            <div>
              Calificación inferida: <strong>{resultadoIa.estrellas_predichas} de 5 estrellas</strong> · Sentimiento:{' '}
              <span style={{ textTransform: 'capitalize' }}>{resultadoIa.sentimiento}</span> ({resultadoIa.confianza}% confianza)
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 600, color: 'var(--ink)', marginBottom: '6px' }}>
              Tu comentario o experiencia sobre el servicio
            </label>
            <textarea
              required
              rows={4}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Ejemplo: La comida llegó a tiempo pero el repartidor no tenía cambio, aunque la atención telefónica fue muy amable..."
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid var(--line)',
                background: 'var(--canvas)',
                fontSize: '13px',
                color: 'var(--ink)',
                boxSizing: 'border-box',
                resize: 'vertical',
                lineHeight: 1.5,
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                padding: '9px 16px',
                borderRadius: '6px',
                border: '1px solid var(--line)',
                background: 'none',
                color: 'var(--muted)',
                fontWeight: 600,
                fontSize: '13px',
                cursor: 'pointer',
              }}
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '9px 22px',
                borderRadius: '6px',
                border: 'none',
                background: 'var(--accent)',
                color: '#ffffff',
                fontWeight: 600,
                fontSize: '13px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? 'El modelo está analizando el texto...' : 'Calcular Estrellas con IA'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}