import type { ApiError } from '../api/client'
import { ErrorNotice, Loading } from '../components/Feedback'
import { Icon } from '../components/Icon'
import { NlpTrace } from '../components/NlpTrace'
import { ReviewForm } from '../components/ReviewForm'
import type { Metrics, NlpTrace as Trace } from '../types/reviewiq'

interface Props {
  text: string
  onChange: (text: string) => void
  onSubmit: () => void
  pending: boolean
  result: Trace | null
  error: ApiError | null
  metrics: Metrics | null
}

export function NlpLabPage({ text, onChange, onSubmit, pending, result, error, metrics }: Props) {
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">LABORATORIO NLP</span>
        <h1 tabIndex={-1}>Del texto a sus rasgos</h1>
        <p>Explora los pasos reales del mismo preprocesador que hace la predicción.</p>
      </div>
      <section className="panel lab-editor">
        <ReviewForm
          text={text}
          onChange={onChange}
          onSubmit={onSubmit}
          pending={pending}
          laboratory
        />
      </section>
      <section
        className="panel lab-output"
        aria-label="Traza del procesamiento"
        aria-busy={pending}
      >
        {pending ? (
          <Loading>Consultando las etapas del preprocesador…</Loading>
        ) : error ? (
          <ErrorNotice error={error} retry={onSubmit} />
        ) : result ? (
          <NlpTrace trace={result} metrics={metrics} />
        ) : (
          <div className="lab-empty">
            <Icon name="nlp" />
            <h2>Abre la caja del procesamiento</h2>
            <p>
              Consulta la normalización, los tokens, las palabras retiradas y los n-gramas de tu
              reseña. Cada etapa llega del servicio de análisis.
            </p>
          </div>
        )}
      </section>
    </>
  )
}
