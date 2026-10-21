import { Icon } from '../components/Icon'

export function AboutPage() {
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">METODOLOGÍA Y ALCANCE</span>
        <h1 tabIndex={-1}>Qué estima ReviewIQ</h1>
        <p>Un proyecto académico para entender reseñas comerciales en español.</p>
      </div>
      <section className="method-intro">
        <div>
          <h2>
            Una valoración estimada,
            <br />
            no la voz del cliente.
          </h2>
          <p>
            El modelo aprende patrones de textos asociados a calificaciones de una a cinco
            estrellas. Una predicción no demuestra satisfacción, intención ni una opinión real de la
            persona que escribió la reseña.
          </p>
        </div>
        <div
          className="method-scale"
          aria-label="Cinco clases: una, dos, tres, cuatro y cinco estrellas"
        >
          {[1, 2, 3, 4, 5].map((value) => (
            <span key={value}>
              <Icon name="star" />
              <strong>{value}</strong>
            </span>
          ))}
        </div>
      </section>
      <section className="method-section">
        <span className="eyebrow">01 / DATOS</span>
        <h2>Reseñas de productos, en español</h2>
        <p>
          Se utiliza el corpus Amazon Reviews Multi, mediante el espejo
          SetFit/amazon_reviews_multi_es. Las particiones originales contienen 200.000 reseñas de
          entrenamiento, 5.000 de validación y 5.000 de test. La preparación deja 197.572 reseñas de
          entrenamiento tras retirar duplicados, conflictos y solapamientos.
        </p>
        <p>
          El corpus está sujeto a condiciones de uso académico. Los textos y los identificadores del
          dataset no se redistribuyen en el repositorio.
        </p>
        <div className="reference-links">
          <a
            href="https://huggingface.co/datasets/SetFit/amazon_reviews_multi_es"
            target="_blank"
            rel="noreferrer"
          >
            Fuente del dataset ↗
          </a>
          <a
            href="https://github.com/awslabs/open-data-docs/blob/main/docs/amazon-reviews-ml/README.md#license"
            target="_blank"
            rel="noreferrer"
          >
            Condiciones de uso ↗
          </a>
        </div>
      </section>
      <section className="method-section">
        <span className="eyebrow">02 / REPRESENTACIÓN Y MODELOS</span>
        <h2>Procesamiento compartido, de principio a fin</h2>
        <ol className="method-pipeline">
          <li>
            Normalización<span>Texto y tokens en español</span>
          </li>
          <li>
            Morfología<span>Stemming o lematización</span>
          </li>
          <li>
            TF-IDF<span>Rasgos de uni/bigramas</span>
          </li>
          <li>
            Clasificación<span>Distribución de cinco estrellas</span>
          </li>
        </ol>
        <p>
          Se compararon Naive Bayes y regresión logística. Los parámetros se ajustaron con
          validación cruzada dentro de train; validation eligió el campeón. El test se evaluó una
          sola vez, después de congelar la selección. La aplicación consulta esas métricas
          guardadas.
        </p>
        <p>
          El laboratorio y la predicción usan los mismos transformadores serializados. Las stop
          words conservan negaciones como «no», «nunca» y «sin»; el lematizador mantiene el contexto
          antes de filtrarlas.
        </p>
      </section>
      <section className="method-section limitations">
        <span className="eyebrow">03 / LÍMITES DE INTERPRETACIÓN</span>
        <h2>El contexto importa</h2>
        <ul>
          <li>
            Las estrellas intermedias pueden ser difíciles de distinguir, incluso cuando el texto
            resulta claro para una persona.
          </li>
          <li>
            Contrastes, ironía, reseñas muy breves y vocabulario desconocido pueden producir
            errores.
          </li>
          <li>
            El español coloquial de Bolivia, otros dialectos o reseñas de restaurantes pueden
            diferir de las reseñas de productos usadas para entrenar.
          </li>
          <li>
            Las probabilidades no se presentan como confianza calibrada. Usa la distribución
            completa y revisa el texto.
          </li>
        </ul>
      </section>
      <section className="method-section">
        <span className="eyebrow">04 / DESARROLLO Y PRIVACIDAD</span>
        <h2>Resultados reales y trazabilidad</h2>
        <p>
          Las reseñas se envían al servicio de análisis configurado y no se guardan en un historial.
          Esta interfaz no almacena los textos en el navegador ni los envía a servicios de
          analítica.
        </p>
        <p>
          Se utilizó asistencia de Codex para implementar código, pruebas y documentación. Las
          predicciones proceden de modelos clásicos entrenados, no de un modelo generativo. Los
          ejemplos del formulario son sintéticos y solo se calculan al solicitar el análisis.
        </p>
      </section>
    </>
  )
}
