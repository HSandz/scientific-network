import { defineConfig, devices } from "@playwright/test";
import path from "path";
import { fileURLToPath } from "url";

const FRONTEND_DIR = path.dirname(fileURLToPath(import.meta.url));
const APP_DIR = path.resolve(FRONTEND_DIR, "..");
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
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:5173",
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
      command: `PYTHONPATH=${APP_DIR}:${REPO_ROOT}/src ${REPO_ROOT}/.venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 8000`,
      cwd: APP_DIR,
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: true,
      timeout: 30_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173",
      cwd: FRONTEND_DIR,
      url: "http://127.0.0.1:5173",
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
