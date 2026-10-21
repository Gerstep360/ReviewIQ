import { useState } from 'react'
import type { ApiError } from '../api/client'
import { ConfusionMatrix } from '../components/ConfusionMatrix'
import { ErrorNotice, Loading } from '../components/Feedback'
import { dateLabel, modelName, morphologyName, number, percent } from '../lib/format'
import type { Metrics } from '../types/reviewiq'

export function ModelsPage({
  data,
  pending,
  error,
  reload,
}: {
  data: Metrics | null
  pending: boolean
  error: ApiError | null
  reload: () => void
}) {
  const [selected, setSelected] = useState('active')
  const compared = data?.comparison?.models || []
  const candidate = selected === 'active' ? null : compared[Number(selected)]
  const values = candidate?.metrics || data?.metrics
  const active = data?.configuration.classifier.name
  const finalTest = !candidate && data?.split === 'test'
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">EVALUACIÓN DEL MODELO</span>
        <h1 tabIndex={-1}>Resultados, con contexto</h1>
        <p>Compara modelos en validación y consulta el test final del modelo activo.</p>
      </div>
      {pending ? (
        <section className="panel">
          <Loading>Consultando las métricas guardadas…</Loading>
        </section>
      ) : error ? (
        <ErrorNotice error={error} retry={reload} title="No se pudieron cargar las métricas" />
      ) : data && values ? (
        <>
          {data.experimental && (
            <p className="notice experimental">
              Paquete rápido experimental: estas métricas son de validación, no de test final.
            </p>
          )}
          <section className="panel comparison-panel">
            <div className="section-heading">
              <h2>Comparación de clasificadores</h2>
              <span className="badge">VALIDACIÓN</span>
            </div>
            <p className="section-description">
              La selección prioriza Macro-F1; en empate, menor MAE. El test final se conserva
              aparte.
            </p>
            {compared.length ? (
              <div className="table-scroll">
                <table className="comparison-table">
                  <caption className="sr-only">Modelos comparados sobre validación</caption>
                  <thead>
                    <tr>
                      <th scope="col">Modelo</th>
                      <th scope="col">Procesamiento</th>
                      <th scope="col">Macro-F1</th>
                      <th scope="col">Accuracy</th>
                      <th scope="col">MAE ★</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compared.map((model, index) => (
                      <tr
                        key={`${model.model}-${index}`}
                        className={model.model === active ? 'active-model' : ''}
                      >
                        <th scope="row">
                          {modelName(model.model)}
                          {model.model === active && (
                            <span className="selected-model-label">Seleccionado en validación</span>
                          )}
                        </th>
                        <td>
                          {morphologyName(model.morphology)}
                          <small>
                            {model.ngram_range[1] === 2 ? 'Uni + bigramas' : 'Unigramas'}
                          </small>
                        </td>
                        <td>{number(model.metrics.macro_f1, 4)}</td>
                        <td>{percent(model.metrics.accuracy, 2)}</td>
                        <td>{number(model.metrics.mae_stars, 4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="notice">
                Este paquete no incluye una comparación de finalistas compatible. Se muestran
                únicamente sus métricas verificadas.
              </p>
            )}
          </section>
          <div className="metric-source">
            <div>
              <label htmlFor="metric-source">Inspeccionar resultados de</label>
              <select
                id="metric-source"
                value={candidate ? selected : 'active'}
                onChange={(event) => setSelected(event.target.value)}
              >
                <option value="active">
                  {modelName(active || '')} ·{' '}
                  {data.split === 'test' ? 'Test final' : 'Validación experimental'} · Modelo activo
                </option>
                {compared.map((model, index) => (
                  <option value={String(index)} key={index}>
                    {modelName(model.model)} · Validación
                  </option>
                ))}
              </select>
            </div>
            <div className="source-caption">
              <span className={`badge ${finalTest ? 'test-badge' : ''}`}>
                {finalTest ? 'TEST FINAL' : 'VALIDACIÓN'}
              </span>
              <span>
                {number(values.rows)} reseñas ·{' '}
                {dateLabel(
                  candidate ? data.comparison?.generated_at_utc || null : data.evaluated_at_utc,
                )}
              </span>
            </div>
          </div>
          <dl className="metric-summary">
            <div>
              <dt>Macro-F1</dt>
              <dd>{number(values.macro_f1, 4)}</dd>
              <p>Equilibrio entre las cinco clases</p>
            </div>
            <div>
              <dt>Accuracy</dt>
              <dd>{percent(values.accuracy, 2)}</dd>
              <p>Predicciones exactas</p>
            </div>
            <div>
              <dt>MAE en estrellas</dt>
              <dd>{number(values.mae_stars, 4)}</dd>
              <p>Distancia media a la valoración real</p>
            </div>
          </dl>
          <div className="evaluation-grid">
            <section className="panel">
              <h2>Matriz de confusión</h2>
              <ConfusionMatrix matrix={values.confusion_matrix} />
            </section>
            <section className="panel">
              <h2>Detalle por estrellas</h2>
              <div className="table-scroll">
                <table className="class-table">
                  <caption className="sr-only">
                    Precisión, recall y F1 por estrellas del conjunto seleccionado
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Estrellas</th>
                      <th scope="col">Precisión</th>
                      <th scope="col">Recall</th>
                      <th scope="col">F1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {values.per_class.map((item) => (
                      <tr key={item.stars}>
                        <th scope="row">
                          {item.stars} ★<small>{number(item.support)} reseñas</small>
                        </th>
                        <td>{percent(item.precision)}</td>
                        <td>{percent(item.recall)}</td>
                        <td>{number(item.f1, 3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
          <section className="configuration">
            <h2>Configuración del paquete activo</h2>
            <dl>
              <div>
                <dt>Clasificador</dt>
                <dd>{modelName(data.configuration.classifier.name)}</dd>
              </div>
              <div>
                <dt>Morfología</dt>
                <dd>{morphologyName(data.configuration.preprocessing.morphology)}</dd>
              </div>
              <div>
                <dt>Vocabulario TF-IDF</dt>
                <dd>
                  {number(data.configuration.feature_count)} rasgos · n-gramas (
                  {data.configuration.tfidf.ngram_range.join(', ')})
                </dd>
              </div>
              <div>
                <dt>Parámetro</dt>
                <dd>
                  {data.configuration.classifier.parameters.C !== undefined
                    ? `C = ${data.configuration.classifier.parameters.C}`
                    : `alpha = ${data.configuration.classifier.parameters.alpha}`}
                </dd>
              </div>
              <div>
                <dt>Semilla</dt>
                <dd>{data.configuration.seed}</dd>
              </div>
              <div>
                <dt>Versión del modelo</dt>
                <dd>
                  <code>{data.model_id}</code>
                </dd>
              </div>
            </dl>
          </section>
          <p className="chart-note">
            Las métricas se leen de informes guardados. Consultar esta página no vuelve a evaluar
            test. Las probabilidades no equivalen a certeza calibrada.
          </p>
        </>
      ) : null}
    </>
  )
}
