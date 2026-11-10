import { defineConfig, devices } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url));
const APP_DIR = path.resolve(FRONTEND_DIR, "..");
const API_PORT = process.env.PLAYWRIGHT_API_PORT || "8000";
const UI_PORT = process.env.PLAYWRIGHT_UI_PORT || "5173";
const REPO_ROOT = path.resolve(APP_DIR, "../..");

export default defineConfig({
  testDir: "./tests",
  outputDir: "/tmp/playwright-test-results",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: "list",
  timeout: 45_000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || `http://127.0.0.1:${UI_PORT}`,
    colorScheme: "dark",
    trace: "off",
    viewport: { width: 1440, height: 900 },
    launchOptions: {
      executablePath: "/usr/bin/google-chrome",
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    },
  },
  webServer: [
    {
      command: `PYTHONPATH=${APP_DIR}:${REPO_ROOT}/src ${REPO_ROOT}/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port ${API_PORT}`,
      cwd: APP_DIR,
      url: `http://127.0.0.1:${API_PORT}/api/health`,
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${UI_PORT}`,
      env: { VITE_API_BASE_URL: "/api", EXPLORER_DEV_API_ORIGIN: `http://127.0.0.1:${API_PORT}` },
      cwd: FRONTEND_DIR,
      url: `http://127.0.0.1:${UI_PORT}`,
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        channel: "chrome",
        launchOptions: {
          executablePath: "/usr/bin/google-chrome",
          args: ["--no-sandbox", "--disable-setuid-sandbox"],
        },
      },
    },
  ],
});
