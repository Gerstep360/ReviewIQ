import { useState } from 'react'
import { syncYouTube } from '../../api/reviewApi'
import type { Entidad } from '../../types/reviewHome'

interface SyncYouTubeModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  entidadActual?: Entidad | null
  entidades?: Entidad[]
}

export function SyncYouTubeModal({
  isOpen,
  onClose,
  onSuccess,
  entidadActual,
  entidades = [],
}: SyncYouTubeModalProps) {
  const [videoUrl, setVideoUrl] = useState('')
  const [entidadId, setEntidadId] = useState<string>(entidadActual?.id || (entidades[0]?.id ?? ''))
  const [cantidad, setCantidad] = useState<number>(30)
  const [loading, setLoading] = useState(false)
  const [progreso, setProgreso] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  // Extraer ID de video para vista previa de miniatura
  const matchId = videoUrl.match(/(?:v=|\/|youtu\.be\/|embed\/|shorts\/)([0-9A-Za-z_-]{11})/)
  const videoId = matchId ? matchId[1] : null

  const entidadElegida = entidadActual || entidades.find((e) => e.id === entidadId)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!videoUrl.trim()) {
      setError('Ingresa el enlace o ID del video de YouTube.')
      return
    }
    const targetId = entidadActual?.id || entidadId
    if (!targetId) {
      setError('Selecciona la aplicación o empresa que se evaluará.')
      return
    }

    setLoading(true)
    setError(null)
    setProgreso('Descargando comentarios del video y analizando con la IA de ReviewIQ...')

    try {
      const res = await syncYouTube({
        entidad_id: targetId,
        video_url: videoUrl.trim(),
        cantidad: cantidad,
      })
      setProgreso(`¡Éxito! Se analizaron ${res.nuevos_comentarios} comentarios nuevos.`)
      setTimeout(() => {
        setLoading(false)
        setProgreso(null)
        setVideoUrl('')
        onSuccess()
        onClose()
      }, 1200)
    } catch (err: any) {
      setError(err.message || 'Error al procesar el video de YouTube.')
      setLoading(false)
      setProgreso(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-lg shadow-2xl p-6 relative">
        <button
          onClick={onClose}
          disabled={loading}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors text-xl font-bold"
        >
          ✕
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-red-600/20 text-red-500 border border-red-500/30 flex items-center justify-center text-xl font-bold">
            ▶
          </div>
          <div>
            <h3 className="text-xl font-semibold text-white">Analizar Opiniones de YouTube</h3>
            <p className="text-xs text-slate-400">
              Extrae comentarios de reseñas, pruebas o críticas y califícalas con IA
            </p>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {progreso && (
          <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2">
            <span className="animate-spin">🔄</span> {progreso}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!entidadActual && entidades.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Aplicación a Evaluar
              </label>
              <select
                value={entidadId}
                onChange={(e) => setEntidadId(e.target.value)}
                disabled={loading}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white text-sm focus:outline-none focus:border-red-500 transition-colors"
              >
                {entidades.map((ent) => (
                  <option key={ent.id} value={ent.id}>
                    {ent.nombre} ({ent.categoria})
                  </option>
                ))}
              </select>
            </div>
          )}

          {entidadElegida && (
            <div className="p-3 bg-slate-800/60 border border-slate-700/50 rounded-xl flex items-center gap-3">
              {entidadElegida.icono_url ? (
                <img
                  src={entidadElegida.icono_url}
                  alt={entidadElegida.nombre}
                  className="w-8 h-8 rounded-lg object-cover"
                />
              ) : (
                <span className="text-lg">📱</span>
              )}
              <div className="text-xs">
                <span className="text-slate-400">Vinculando opiniones a:</span>{' '}
                <strong className="text-white">{entidadElegida.nombre}</strong>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Enlace o ID del Video de YouTube
            </label>
            <input
              type="text"
              placeholder="https://www.youtube.com/watch?v=... o youtu.be/..."
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              disabled={loading}
              className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3.5 py-2.5 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-red-500 transition-colors"
            />
          </div>

          {videoId && (
            <div className="relative rounded-xl overflow-hidden border border-slate-700/60 bg-black/40">
              <img
                src={`https://img.youtube.com/vi/${videoId}/hqdefault.jpg`}
                alt="Vista previa del video"
                className="w-full h-32 object-cover opacity-80"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent flex items-end p-2.5">
                <span className="text-xs text-white bg-red-600/80 px-2 py-0.5 rounded font-medium flex items-center gap-1">
                  ▶ Video detectado ({videoId})
                </span>
              </div>
            </div>
          )}

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Límite de Comentarios a Procesar
              </label>
              <span className="text-xs font-bold text-red-400">{cantidad} comentarios</span>
            </div>
            <input
              type="range"
              min={10}
              max={100}
              step={10}
              value={cantidad}
              onChange={(e) => setCantidad(Number(e.target.value))}
              disabled={loading}
              className="w-full accent-red-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-400 mt-1">
              <span>10 rápidos</span>
              <span>30 balanceado</span>
              <span>100 profundo</span>
            </div>
          </div>

          <div className="p-3 bg-red-950/20 border border-red-500/20 rounded-xl text-xs text-slate-300 leading-relaxed">
            💡 <strong>¿Cómo funciona?</strong> En YouTube los usuarios no eligen estrellas. La IA de ReviewIQ
            analiza el texto de cada comentario, predice su calificación (1–5★), detecta elogios o quejas en las 5 dimensiones
            y recalcula el Semáforo de la app.
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading || !videoUrl.trim()}
              className="px-5 py-2 text-sm font-semibold rounded-xl bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg shadow-red-500/20 hover:from-red-500 hover:to-rose-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <span className="animate-spin text-sm">🔄</span>
                  Procesando con IA...
                </>
              ) : (
                'Iniciar Análisis'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

