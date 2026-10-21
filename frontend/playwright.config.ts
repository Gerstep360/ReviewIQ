import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './tests/browser',
  workers: 1,
  retries: 0,
  timeout: 45_000,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    viewport: { width: 1366, height: 768 },
    locale: 'es-BO',
    colorScheme: 'light',
    reducedMotion: 'reduce',
    screenshot: 'only-on-failure',
  },
  reporter: 'list',
  webServer: [
    {
      command: `${process.platform === 'win32' ? '../venv/Scripts/python.exe' : '../venv/bin/python'} ../manage.py runapi 127.0.0.1:8000 --noreload --nothreading`,
      url: 'http://127.0.0.1:8000/api/v1/health/',
      reuseExistingServer: true,
      timeout: 30_000,
      env: { OMP_NUM_THREADS: '1', OPENBLAS_NUM_THREADS: '1', MKL_NUM_THREADS: '1' },
    },
    {
      command: 'npm run preview',
      url: 'http://127.0.0.1:4173',
      reuseExistingServer: true,
      timeout: 20_000,
    },
    {
      command: 'npm run dev',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 20_000,
    },
  ],
})
