import type { ApiError } from '../api/client'
import { ErrorNotice, Loading } from '../components/Feedback'
import { Icon } from '../components/Icon'
import { ProbabilityBars } from '../components/ProbabilityBars'
import { ReviewForm } from '../components/ReviewForm'
import { number, percent } from '../lib/format'
import { STAR_VALUES } from '../types/reviewiq'
import type { Prediction } from '../types/reviewiq'

interface Props {
  text: string
  onChange: (text: string) => void
  onSubmit: () => void
  pending: boolean
  result: Prediction | null
  error: ApiError | null
  inspect: () => void
}

export function PredictPage({ text, onChange, onSubmit, pending, result, error, inspect }: Props) {
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">PREDICCIÓN DE ESTRELLAS</span>
        <h1 tabIndex={-1}>Analiza una reseña</h1>
        <p>Una estimación de 1 a 5 estrellas, acompañada de su evidencia.</p>
      </div>
      <div className="prediction-layout">
        <section className="panel editor-panel" aria-label="Entrada de reseña">
          <ReviewForm text={text} onChange={onChange} onSubmit={onSubmit} pending={pending} />
        </section>
        <section
          className={`panel result-panel ${result ? 'has-result' : ''}`}
          aria-label="Resultado del análisis"
          aria-busy={pending}
        >
          <div className="section-heading">
            <h2 id="analysis-result-title" tabIndex={-1}>
              Estimación del modelo
            </h2>
            <span className="eyebrow">1–5 ESTRELLAS</span>
          </div>
          {pending ? (
            <Loading>El modelo está analizando tu reseña…</Loading>
          ) : error ? (
            <ErrorNotice error={error} retry={onSubmit} title="El análisis no pudo completarse" />
          ) : result ? (
            <div className="prediction-result" aria-live="polite">
              {result.experimental && (
                <p className="notice experimental">Modelo rápido · Resultado experimental</p>
              )}
              <div className="rating-result">
                <span className="rating-number">
                  {result.stars}
                  <span>/5</span>
                </span>
                <div>
                  <div className="stars" role="img" aria-label={`${result.stars} de 5 estrellas`}>
                    {STAR_VALUES.map((stars) => (
                      <Icon
                        key={stars}
                        name="star"
                        className={stars <= result.stars ? 'filled-star' : 'empty-star'}
                      />
                    ))}
                  </div>
                  <p>{percent(result.probabilities[result.stars])} para esta categoría</p>
                </div>
              </div>
              <ProbabilityBars probabilities={result.probabilities} selected={result.stars} />
              <p className="probability-disclaimer">
                Probabilidades estimadas del modelo. No representan certeza calibrada ni una
                valoración real del cliente.
              </p>
              <dl className="prediction-meta">
                <div>
                  <dt>Clase interna</dt>
                  <dd>{result.label}</dd>
                </div>
                <div>
                  <dt>Inferencia</dt>
                  <dd>{number(result.inference_ms, 2)} ms</dd>
                </div>
              </dl>
              <div className="model-line">
                <span>Modelo</span>
                <code>{result.model_id}</code>
              </div>
              <button className="inspect-button" type="button" onClick={inspect}>
                Ver cómo se procesó el texto
                <Icon name="arrow" />
              </button>
            </div>
          ) : (
            <div className="empty-result">
              <div className="empty-stars" aria-hidden="true">
                {STAR_VALUES.map((stars) => (
                  <span key={stars}>
                    <Icon name="star" />
                    {stars}
                  </span>
                ))}
              </div>
              <h3>Cada reseña tiene matices</h3>
              <p>Escribe tu reseña y analiza cómo se distribuye entre las cinco valoraciones.</p>
              <span className="empty-result-note">
                Aquí aparecerá un resultado calculado por el modelo.
              </span>
            </div>
          )}
        </section>
      </div>
      <aside className="context-strip">
        <Icon name="book" />
        <div>
          <strong>Texto comercial en español</strong>
          <p>
            Entrenado con reseñas de productos. Las valoraciones intermedias y el lenguaje fuera de
            este dominio pueden ser más difíciles de interpretar.
          </p>
        </div>
      </aside>
    </>
  )
}
