import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [react()],
  test: {
    include: ['src/tests/**/*.test.{ts,tsx}'],
    environment: 'jsdom',
    setupFiles: ['src/tests/setup.ts'],
    maxWorkers: 1,
    fileParallelism: false,
  },
})
