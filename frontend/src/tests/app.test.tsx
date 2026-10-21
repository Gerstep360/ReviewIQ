import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import App from '../App'
import { predict } from '../api/client'
import { ModelsPage } from '../pages/ModelsPage'
import type { Metrics, NlpTrace, Prediction } from '../types/reviewiq'

// Fixtures sintéticos exclusivos de tests. No se importan desde el producto.
const prediction: Prediction = {
  stars: 4,
  label: 3,
  probabilities: { 1: 0.05, 2: 0.1, 3: 0.15, 4: 0.6, 5: 0.1 },
  model_id: 'synthetic-ui-fixture',
  inference_ms: 9.5,
  experimental: false,
}
const metricValues = {
  rows: 5,
  macro_f1: 1,
  accuracy: 1,
  mae_stars: 0,
  per_class: [1, 2, 3, 4, 5].map((stars) => ({
    label: stars - 1,
    stars,
    precision: 1,
    recall: 1,
    f1: 1,
    support: 1,
  })),
  confusion_matrix: [0, 1, 2, 3, 4].map((row) => [0, 1, 2, 3, 4].map((col) => Number(row === col))),
}
const metrics = {
  model_id: prediction.model_id,
  mode: 'full',
  split: 'test',
  experimental: false,
  evaluated_at_utc: '2026-01-01T00:00:00Z',
  packaged_at_utc: '2026-01-01T00:00:00Z',
  dataset: { repository: 'synthetic-fixture', revision: 'synthetic-revision' },
  configuration: {
    preprocessing: { morphology: 'lemmatization', preserve_accents: true, protect_negations: true },
    tfidf: { ngram_range: [1, 2], max_features: 50, min_df: 1, max_df: 1, sublinear_tf: true },
    classifier: { name: 'LogisticRegression', parameters: { C: 1 } },
    feature_count: 50,
    seed: 42,
  },
  metrics: metricValues,
  comparison: {
    model_id: prediction.model_id,
    split: 'validation',
    generated_at_utc: '2026-01-01T00:00:00Z',
    models: ['MultinomialNB', 'LogisticRegression'].map((model) => ({
      model,
      morphology: 'lemmatization',
      ngram_range: [1, 2],
      best_params: {},
      train_rows: 5,
      metrics: metricValues,
    })),
  },
  probability_notice: 'Synthetic fixture only',
} as Metrics
const trace: NlpTrace = {
  model_id: prediction.model_id,
  original: 'NO, funciona',
  normalized: 'normalizado_por_backend',
  tokens: ['TOKEN_DEL_SERVIDOR', 'no'],
  removed_stopwords: [],
  tokens_after_stopwords: ['TOKEN_DEL_SERVIDOR', 'no'],
  processed_tokens: ['lema_servidor', 'no'],
  processed_text: 'lema_servidor no',
  method: 'lemmatization',
  policy_version: 'synthetic-policy',
  stopwords_version: 'synthetic-stopwords',
  stopwords_sha256: 'synthetic-hash',
  ngram_range: [1, 2],
  ngrams: ['rasgo_api'],
  known_ngrams: ['rasgo_api'],
  unknown_ngrams: [],
  truncated: false,
  limits: { items_per_list: 200, characters_per_string: 12000 },
  original_counts: {
    tokens: 2,
    removed_stopwords: 0,
    processed_tokens: 2,
    ngrams: 1,
    known_ngrams: 1,
    unknown_ngrams: 0,
  },
}
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } })

function installFetch(
  post: (url: string, options?: RequestInit) => Promise<Response> = vi.fn(async () =>
    json(prediction),
  ),
) {
  const fetch = vi.fn((url: string, options?: RequestInit) => {
    if (url.endsWith('/health/'))
      return Promise.resolve(
        json({ status: 'ok', model_loaded: true, model_id: prediction.model_id, mode: 'full' }),
      )
    if (url.endsWith('/metrics/')) return Promise.resolve(json(metrics))
    if (url.endsWith('/nlp/trace/')) return Promise.resolve(json(trace))
    return post(url, options)
  })
  vi.stubGlobal('fetch', fetch)
  return fetch
}

describe('Frontend conectado al contrato REST', () => {
  it('valida blancos, cuenta Unicode como la API y rechaza 3001 caracteres sin enviar', async () => {
    const fetch = installFetch()
    render(<App />)
    await screen.findByText('API conectada')
    const input = screen.getByRole('textbox', { name: 'Tu reseña' })
    const button = screen.getByRole('button', { name: 'Analizar reseña' }) as HTMLButtonElement
    expect(button.disabled).toBe(true)
    fireEvent.change(input, { target: { value: '  ' } })
    expect(button.disabled).toBe(true)
    fireEvent.change(input, { target: { value: '🙂'.repeat(3000) } })
    expect(button.disabled).toBe(false)
    fireEvent.change(input, { target: { value: 'a'.repeat(3001) } })
    expect(button.disabled).toBe(true)
    expect(screen.getByRole('alert').textContent).toContain('3.000')
    expect(fetch.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(0)
  })

  it('envía un ejemplo solo al analizar, muestra carga y cinco probabilidades reales de la respuesta', async () => {
    let release: () => void = () => undefined
    const waiting = new Promise<void>((resolve) => {
      release = resolve
    })
    const fetch = installFetch(
      vi.fn(async () => {
        await waiting
        return json(prediction)
      }),
    )
    render(<App />)
    await screen.findByText('API conectada')
    fireEvent.click(screen.getByRole('button', { name: 'Positiva' }))
    expect(fetch.mock.calls.filter(([, options]) => options?.method === 'POST')).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Analizar reseña' }))
    expect(
      (screen.getByRole('button', { name: 'Analizando…' }) as HTMLButtonElement).disabled,
    ).toBe(true)
    await act(async () => release())
    await screen.findByRole('img', { name: '4 de 5 estrellas' })
    const chart = screen.getByRole('group', { name: 'Probabilidades por estrellas' })
    expect(within(chart).getByText('60,0 %')).toBeTruthy()
    expect(chart.querySelectorAll('.probability-row')).toHaveLength(5)
    const sent = fetch.mock.calls.find(([, options]) => options?.method === 'POST')
    expect(JSON.parse(String(sent?.[1]?.body)).text).toContain('Excelente calidad')
    expect(screen.getByText('9,50 ms')).toBeTruthy()
  })

  it('muestra un fallo de red y permite reintentar conservando el texto', async () => {
    installFetch(
      vi
        .fn()
        .mockRejectedValueOnce(new TypeError('Failed to fetch'))
        .mockResolvedValue(json(prediction)),
    )
    render(<App />)
    await screen.findByText('API conectada')
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Mi reseña de prueba' } })
    fireEvent.click(screen.getByRole('button', { name: 'Analizar reseña' }))
    expect((await screen.findByRole('alert')).textContent).toContain('No hay conexión')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    await screen.findByRole('img', { name: '4 de 5 estrellas' })
    expect((screen.getByRole('textbox') as HTMLTextAreaElement).value).toBe('Mi reseña de prueba')
  })

  it('muestra tokens del backend y retira la traza al editar, sin tokenizar en JS', async () => {
    installFetch()
    window.location.hash = '/laboratorio'
    render(<App />)
    await screen.findByText('API conectada')
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'NO, funciona' } })
    fireEvent.click(screen.getByRole('button', { name: 'Ver procesamiento NLP' }))
    expect(await screen.findByText('TOKEN_DEL_SERVIDOR')).toBeTruthy()
    expect(screen.getByText('normalizado_por_backend')).toBeTruthy()
    expect(screen.getByText('lema_servidor')).toBeTruthy()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'Otra reseña' } })
    expect(screen.queryByText('TOKEN_DEL_SERVIDOR')).toBeNull()
    expect(screen.getByText('Abre la caja del procesamiento')).toBeTruthy()
  })

  it('separa test de validación y cambia la matriz y el detalle por clase del modelo seleccionado', () => {
    render(<ModelsPage data={metrics} pending={false} error={null} reload={vi.fn()} />)
    expect(screen.getByText('TEST FINAL')).toBeTruthy()
    expect(
      screen.getByRole('table', { name: /Matriz de confusión/ }).querySelectorAll('td'),
    ).toHaveLength(25)
    fireEvent.change(screen.getByLabelText('Inspeccionar resultados de'), {
      target: { value: '0' },
    })
    expect(screen.queryByText('TEST FINAL')).toBeNull()
    expect(
      (screen.getByRole('combobox') as HTMLSelectElement).selectedOptions[0].textContent,
    ).toContain('Naive Bayes · Validación')
    expect(
      screen.getByRole('table', { name: /Precisión, recall/ }).querySelectorAll('tbody tr'),
    ).toHaveLength(5)
  })

  it('rechaza probabilidades inválidas y termina solicitudes por timeout sin inventar un resultado', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => json({ ...prediction, probabilities: { 1: 1, 2: 1, 3: 1, 4: 1, 5: 1 } })),
    )
    await expect(predict('Texto sintético')).rejects.toMatchObject({ code: 'invalid_response' })
    vi.useFakeTimers()
    vi.stubGlobal(
      'fetch',
      vi.fn(
        (_url, options) =>
          new Promise((_resolve, reject) =>
            options.signal.addEventListener('abort', () =>
              reject(new DOMException('Aborted', 'AbortError')),
            ),
          ),
      ),
    )
    const assertion = expect(predict('Texto sintético')).rejects.toMatchObject({ code: 'timeout' })
    await vi.advanceTimersByTimeAsync(15_001)
    await assertion
  })
})
