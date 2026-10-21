import type { Health, Metrics, NlpTrace, Prediction } from '../types/reviewiq'

const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
const TIMEOUT_MS = 15_000

export class ApiError extends Error {
  code: string
  status: number
  constructor(message: string, code = 'network_error', status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value)
const finite = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value)
const strings = (value: unknown): value is string[] =>
  Array.isArray(value) && value.every((item) => typeof item === 'string')

function validPrediction(value: unknown): value is Prediction {
  if (!record(value) || !record(value.probabilities)) return false
  const probabilities = value.probabilities
  const values = ['1', '2', '3', '4', '5'].map((key) => probabilities[key])
  const stars = value.stars
  return (
    finite(stars) &&
    Number.isInteger(stars) &&
    stars >= 1 &&
    stars <= 5 &&
    value.label === stars - 1 &&
    Object.keys(probabilities).length === 5 &&
    values.every((item) => finite(item) && item >= 0 && item <= 1) &&
    Math.abs((values as number[]).reduce((sum, item) => sum + item, 0) - 1) < 1e-5 &&
    probabilities[String(stars)] === Math.max(...(values as number[])) &&
    typeof value.model_id === 'string' &&
    finite(value.inference_ms) &&
    value.inference_ms >= 0 &&
    typeof value.experimental === 'boolean'
  )
}

function metricValues(value: unknown): boolean {
  return (
    record(value) &&
    finite(value.rows) &&
    value.rows > 0 &&
    ['macro_f1', 'accuracy', 'mae_stars'].every((key) => finite(value[key])) &&
    Array.isArray(value.per_class) &&
    value.per_class.length === 5 &&
    value.per_class.every(
      (item, index) =>
        record(item) &&
        item.stars === index + 1 &&
        ['precision', 'recall', 'f1', 'support'].every((key) => finite(item[key])),
    ) &&
    Array.isArray(value.confusion_matrix) &&
    value.confusion_matrix.length === 5 &&
    value.confusion_matrix.every(
      (row) =>
        Array.isArray(row) &&
        row.length === 5 &&
        row.every((item) => finite(item) && Number.isInteger(item) && item >= 0),
    )
  )
}

function validMetrics(value: unknown): value is Metrics {
  if (
    !record(value) ||
    typeof value.model_id !== 'string' ||
    !metricValues(value.metrics) ||
    !record(value.configuration)
  )
    return false
  const config = value.configuration
  if (
    !record(config.preprocessing) ||
    !record(config.tfidf) ||
    !record(config.classifier) ||
    !record(config.classifier.parameters) ||
    typeof config.classifier.name !== 'string' ||
    typeof config.preprocessing.morphology !== 'string' ||
    !finite(config.feature_count) ||
    !Array.isArray(config.tfidf.ngram_range) ||
    !record(value.dataset) ||
    typeof value.dataset.repository !== 'string' ||
    typeof value.dataset.revision !== 'string'
  )
    return false
  if (value.comparison !== null) {
    const comparison = value.comparison
    if (
      !record(comparison) ||
      comparison.model_id !== value.model_id ||
      comparison.split !== 'validation' ||
      !Array.isArray(comparison.models) ||
      !comparison.models.every(
        (item) =>
          record(item) &&
          typeof item.model === 'string' &&
          typeof item.morphology === 'string' &&
          Array.isArray(item.ngram_range) &&
          record(item.best_params) &&
          metricValues(item.metrics),
      )
    )
      return false
  }
  return (
    ((value.mode === 'full' && value.split === 'test' && value.experimental === false) ||
      (value.mode === 'quick' && value.split === 'validation' && value.experimental === true)) &&
    typeof value.packaged_at_utc === 'string'
  )
}

function validTrace(value: unknown): value is NlpTrace {
  if (!record(value) || !record(value.original_counts)) return false
  const counts = value.original_counts
  return (
    record(value) &&
    [
      'model_id',
      'original',
      'normalized',
      'processed_text',
      'policy_version',
      'stopwords_version',
      'stopwords_sha256',
    ].every((key) => typeof value[key] === 'string') &&
    [
      'tokens',
      'removed_stopwords',
      'tokens_after_stopwords',
      'processed_tokens',
      'ngrams',
      'known_ngrams',
      'unknown_ngrams',
    ].every((key) => strings(value[key])) &&
    [
      'tokens',
      'removed_stopwords',
      'processed_tokens',
      'ngrams',
      'known_ngrams',
      'unknown_ngrams',
    ].every((key) => finite(counts[key]) && counts[key] >= 0) &&
    (value.method === 'stemming' || value.method === 'lemmatization') &&
    Array.isArray(value.ngram_range) &&
    typeof value.truncated === 'boolean' &&
    record(value.original_counts) &&
    record(value.limits)
  )
}

async function request<T>(
  path: string,
  check: (value: unknown) => value is T,
  text?: string,
  signal?: AbortSignal,
): Promise<T> {
  const controller = new AbortController()
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  if (signal?.aborted) controller.abort()
  let timedOut = false
  const timer = setTimeout(() => {
    timedOut = true
    controller.abort()
  }, TIMEOUT_MS)
  try {
    const response = await fetch(base + path, {
      method: text === undefined ? 'GET' : 'POST',
      headers: {
        Accept: 'application/json',
        ...(text === undefined ? {} : { 'Content-Type': 'application/json' }),
      },
      body: text === undefined ? undefined : JSON.stringify({ text }),
      signal: controller.signal,
      cache: 'no-store',
      credentials: 'omit',
    })
    const value: unknown = await response.json().catch(() => null)
    if (!response.ok) {
      const error = record(value) && record(value.error) ? value.error : null
      const fields = error && record(error.fields) ? error.fields : null
      const fieldMessage = fields && strings(fields.text) ? fields.text[0] : undefined
      throw new ApiError(
        fieldMessage ||
          (typeof error?.message === 'string'
            ? error.message
            : 'No se pudo completar la solicitud. Vuelve a intentarlo.'),
        typeof error?.code === 'string' ? error.code : 'service_error',
        response.status,
      )
    }
    if (!check(value))
      throw new ApiError(
        'La respuesta del servicio no tiene el formato esperado. Vuelve a conectar.',
        'invalid_response',
      )
    return value
  } catch (error) {
    if (signal?.aborted) throw error
    if (timedOut)
      throw new ApiError(
        'El servicio tardó demasiado en responder. Vuelve a intentarlo.',
        'timeout',
      )
    if (error instanceof ApiError) throw error
    throw new ApiError(
      'No hay conexión con el servicio de análisis. Comprueba que esté disponible y vuelve a intentarlo.',
    )
  } finally {
    clearTimeout(timer)
    signal?.removeEventListener('abort', cancel)
  }
}

export const getHealth = (signal?: AbortSignal) =>
  request<Health>(
    '/health/',
    (value): value is Health =>
      record(value) &&
      value.status === 'ok' &&
      value.model_loaded === true &&
      typeof value.model_id === 'string' &&
      (value.mode === 'full' || value.mode === 'quick'),
    undefined,
    signal,
  )
export const getMetrics = (signal?: AbortSignal) =>
  request('/metrics/', validMetrics, undefined, signal)
export const predict = (text: string, signal?: AbortSignal) =>
  request('/predict/', validPrediction, text, signal)
export const traceNlp = (text: string, signal?: AbortSignal) =>
  request('/nlp/trace/', validTrace, text, signal)
