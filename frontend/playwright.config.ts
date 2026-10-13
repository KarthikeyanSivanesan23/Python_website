import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests', timeout: 120000, expect: { timeout: 15000 }, workers: 1,
  use: { baseURL: 'http://127.0.0.1:5174', browserName: 'chromium', channel: 'chrome', headless: true, viewport: { width: 1440, height: 1000 }, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: [
    { command: '.venv\\Scripts\\python.exe manage.py runserver 127.0.0.1:8001 --noreload', cwd: '../backend', url: 'http://127.0.0.1:8001/api/session/', reuseExistingServer: process.env.REUSE_DEV_SERVERS === 'true', timeout: 30000, env: { DJANGO_DEBUG: 'true', USE_SQLITE: process.env.USE_SQLITE || 'true', OLLAMA_MODEL: process.env.OLLAMA_MODEL || 'qwen2.5:1.5b' } },
    { command: 'npm run dev', url: 'http://127.0.0.1:5174', reuseExistingServer: process.env.REUSE_DEV_SERVERS === 'true', timeout: 30000 },
  ],
})
