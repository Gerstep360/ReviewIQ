import { test, expect } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

test('las cuatro vistas funcionan con la API real en escritorio y móvil', async ({
  page,
  request,
  browser,
}) => {
  const errors: string[] = []
  page.on('pageerror', (error) => {
    errors.push(error.message)
    console.error(error.message)
  })
  page.on('console', (message) => {
    if (message.type() === 'error') console.error('Browser console: ' + message.text())
  })
  const root = resolve('..')
  const figures = resolve(root, 'reports/figures')
  await mkdir(figures, { recursive: true })
  const api = await request.get('http://127.0.0.1:8000/api/v1/metrics/')
  expect(api.ok()).toBeTruthy()
  const metrics = await api.json()
  await page.goto('http://127.0.0.1:5173/')
  await expect(page.getByRole('heading', { name: 'Analiza una reseña' })).toBeVisible()
  await expect(page.getByText('API conectada', { exact: true })).toBeVisible()
  await page.goto('/')
  await expect(page.getByText('API conectada', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Analizar reseña' })).toBeDisabled()
  await page.screenshot({ path: resolve(figures, 'web-empty-desktop.png') })

  // El ejemplo rellena el formulario; solo el botón de análisis envía el texto.
  let predictionRequests = 0
  page.on('request', (req) => {
    if (req.url().endsWith('/predict/')) predictionRequests++
  })
  await page.getByRole('button', { name: 'Con contraste', exact: true }).click()
  expect(predictionRequests).toBe(0)
  const predictionResponse = page.waitForResponse(
    (response) => response.url().endsWith('/predict/') && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Analizar reseña' }).click()
  const prediction = await (await predictionResponse).json()
  await expect(page.getByRole('img', { name: `${prediction.stars} de 5 estrellas` })).toBeVisible()
  expect(prediction.model_id).toBe(metrics.model_id)
  expect(
    Object.values(prediction.probabilities).reduce((sum: number, value: number) => sum + value, 0),
  ).toBeCloseTo(1, 5)
  expect(await page.locator('.probability-row').count()).toBe(5)
  await page.screenshot({ path: resolve(figures, 'web-prediction-desktop.png') })

  const traceResponse = page.waitForResponse(
    (response) => response.url().endsWith('/nlp/trace/') && response.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Ver cómo se procesó el texto' }).click()
  const trace = await (await traceResponse).json()
  await expect(page.getByRole('heading', { name: 'Así se representa tu reseña' })).toBeVisible()
  await expect(page.locator('.trace-text')).toHaveText(trace.normalized)
  expect(trace.model_id).toBe(prediction.model_id)
  expect(
    await page.locator('.trace-stages .token-section').first().locator('.token').allTextContents(),
  ).toEqual(trace.tokens)
  await page.screenshot({ path: resolve(figures, 'web-nlp-desktop.png'), fullPage: true })

  await page.getByRole('link', { name: 'Modelos y métricas' }).click()
  await expect(page.getByText('TEST FINAL', { exact: true })).toBeVisible()
  const f1 = new Intl.NumberFormat('es-BO', {
    minimumFractionDigits: 4,
    maximumFractionDigits: 4,
  }).format(metrics.metrics.macro_f1)
  await expect(page.locator('.metric-summary')).toContainText(f1)
  expect(await page.locator('.confusion-matrix td').allTextContents()).toEqual(
    metrics.metrics.confusion_matrix
      .flat()
      .map((value: number) => new Intl.NumberFormat('es-BO').format(value)),
  )
  await page.screenshot({ path: resolve(figures, 'web-models-desktop.png'), fullPage: true })
  await page.getByRole('combobox').selectOption('0')
  await expect(page.getByText('TEST FINAL', { exact: true })).toHaveCount(0)
  expect(await page.locator('.confusion-matrix td').allTextContents()).toEqual(
    metrics.comparison.models[0].metrics.confusion_matrix
      .flat()
      .map((value: number) => new Intl.NumberFormat('es-BO').format(value)),
  )
  await page.getByRole('link', { name: 'Metodología', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Qué estima ReviewIQ' })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Fuente del dataset' })).toBeVisible()

  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('link', { name: 'Predicción', exact: true }).click()
  await expect(page.getByRole('textbox')).not.toBeEmpty()
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.screenshot({ path: resolve(figures, 'web-prediction-mobile.png'), fullPage: true })
  await page.getByRole('link', { name: 'Laboratorio NLP', exact: true }).click()
  await expect(page.locator('.trace-text')).toHaveText(trace.normalized)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.getByRole('link', { name: 'Modelos y métricas' }).click()
  await expect(page.locator('.confusion-matrix td')).toHaveCount(25)
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  )
  await page.screenshot({ path: resolve(figures, 'web-models-mobile.png'), fullPage: true })

  // Solo esta respuesta 503 se simula para verificar el estado de error de la UI.
  await page.getByRole('link', { name: 'Predicción', exact: true }).click()
  await page.route('**/api/v1/predict/', (route) =>
    route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({
        error: {
          code: 'model_busy',
          message: 'El modelo está ocupado. Intenta nuevamente en unos segundos.',
        },
      }),
    }),
  )
  await page.getByRole('button', { name: 'Analizar reseña' }).click()
  await expect(page.getByRole('alert')).toContainText('El modelo está ocupado')
  await page.screenshot({ path: resolve(figures, 'web-error-mobile.png'), fullPage: true })
  await page.unroute('**/api/v1/predict/')
  await page.getByRole('button', { name: 'Reintentar', exact: true }).click()
  await expect(page.getByRole('img', { name: `${prediction.stars} de 5 estrellas` })).toBeVisible()
  expect(errors).toEqual([])
  await writeFile(
    resolve(root, 'reports/frontend_smoke.json'),
    JSON.stringify(
      {
        checked_at_utc: new Date().toISOString(),
        browser: browser.version(),
        model_id: prediction.model_id,
        scope:
          'Vite dev plus built frontend via preview proxy and actual Django API. One browser smoke flow, not production load testing.',
        viewports: [
          { width: 1366, height: 768 },
          { width: 390, height: 844 },
        ],
        views: ['prediction', 'nlp', 'models', 'methodology'],
        prediction_stars: prediction.stars,
        probabilities_sum_to_one: true,
        trace_matches_api: true,
        matrices_match_api: true,
        validation_and_test_distinguished: true,
        mobile_page_overflow: false,
        retry_after_simulated_503: 'real API prediction succeeded',
        browser_page_errors: errors,
        screenshots: [
          'web-empty-desktop',
          'web-prediction-desktop',
          'web-nlp-desktop',
          'web-models-desktop',
          'web-prediction-mobile',
          'web-models-mobile',
          'web-error-mobile',
        ].map((name) => `reports/figures/${name}.png`),
        test_evaluation_repeated: false,
      },
      null,
      2,
    ) + '\n',
    'utf-8',
  )
})
