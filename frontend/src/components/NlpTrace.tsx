import { morphologyName, number } from '../lib/format'
import type { Metrics, NlpTrace as Trace } from '../types/reviewiq'

function Tokens({
  title,
  values,
  total,
  tone = '',
}: {
  title: string
  values: string[]
  total: number
  tone?: string
}) {
  return (
    <details className={`token-section ${tone}`} open>
      <summary>
        {title}
        <span>{number(total)}</span>
      </summary>
      {values.length ? (
        <div className="tokens">
          {values.map((token, index) => (
            <span key={`${index}-${token}`} className="token">
              {token}
            </span>
          ))}
        </div>
      ) : (
        <p className="muted empty-tokens">No se encontraron elementos en esta etapa.</p>
      )}
      {total > values.length && (
        <p className="chart-note">
          Se muestran {number(values.length)} de {number(total)} elementos.
        </p>
      )}
    </details>
  )
}

export function NlpTrace({ trace, metrics }: { trace: Trace; metrics: Metrics | null }) {
  const config = metrics?.model_id === trace.model_id ? metrics.configuration : null
  return (
    <div className="trace-result">
      <div className="trace-heading">
        <div>
          <span className="eyebrow">TRAZA DEL MODELO ACTIVO</span>
          <h2 id="trace-result-title" tabIndex={-1}>
            Así se representa tu reseña
          </h2>
        </div>
        <span className="badge">{morphologyName(trace.method)}</span>
      </div>
      {trace.truncated && (
        <p className="notice" role="status">
          La traza fue recortada para facilitar su lectura. Los contadores conservan los tamaños
          originales.
        </p>
      )}
      <section className="normalized-section">
        <span className="step-number">01</span>
        <div>
          <h3>Texto normalizado</h3>
          <p className="trace-text">
            {trace.normalized || 'El texto quedó vacío tras la normalización.'}
          </p>
        </div>
      </section>
      <div className="trace-stages">
        <div>
          <span className="step-number">02</span>
          <Tokens
            title="Tokens del normalizador"
            values={trace.tokens}
            total={trace.original_counts.tokens}
          />
        </div>
        <div>
          <span className="step-number">03</span>
          <Tokens
            title="Stop words retiradas"
            values={trace.removed_stopwords}
            total={trace.original_counts.removed_stopwords}
            tone="removed"
          />
        </div>
        <div>
          <span className="step-number">04</span>
          <Tokens
            title={trace.method === 'lemmatization' ? 'Lemas finales' : 'Raíces finales'}
            values={trace.processed_tokens}
            total={trace.original_counts.processed_tokens}
            tone="processed"
          />
        </div>
        <div>
          <span className="step-number">05</span>
          <Tokens
            title={trace.ngram_range[1] === 2 ? 'Unigramas y bigramas' : 'Unigramas'}
            values={trace.ngrams}
            total={trace.original_counts.ngrams}
          />
        </div>
      </div>
      <section className="vocabulary-section">
        <h3>Del texto al vocabulario TF-IDF</h3>
        <p className="muted">
          Las coincidencias se consultan en el vectorizador guardado; no se vuelve a ajustar.
        </p>
        <div className="vocabulary-facts">
          <div>
            <strong>{config ? number(config.feature_count) : '—'}</strong>
            <span>Rasgos del vocabulario{!config ? ' · metadatos no disponibles' : ''}</span>
          </div>
          <div>
            <strong>{number(trace.original_counts.known_ngrams)}</strong>
            <span>Ocurrencias reconocidas</span>
          </div>
          <div>
            <strong>{number(trace.original_counts.unknown_ngrams)}</strong>
            <span>Ocurrencias fuera del vocabulario</span>
          </div>
        </div>
        <Tokens
          title="N-gramas reconocidos"
          values={trace.known_ngrams}
          total={trace.original_counts.known_ngrams}
          tone="processed"
        />
        <Tokens
          title="N-gramas desconocidos"
          values={trace.unknown_ngrams}
          total={trace.original_counts.unknown_ngrams}
        />
      </section>
      <p className="chart-note">
        {trace.method === 'lemmatization'
          ? 'El lematizador conserva el contexto antes de retirar stop words. '
          : ''}
        {config?.preprocessing.protect_negations
          ? 'Se protegen negaciones como «no», «nunca» y «sin». '
          : ''}
        Los contadores de n-gramas incluyen repeticiones; no son pesos TF-IDF.
      </p>
      <div className="model-line">
        <span>Modelo</span>
        <code>{trace.model_id}</code>
        <span>Política {trace.policy_version}</span>
      </div>
    </div>
  )
}
