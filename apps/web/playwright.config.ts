import { defineConfig, devices } from "@playwright/test";

// S1-приймання: скриншоти головної та пошуку, getComputedStyle шрифтів,
// один «AI Ugoda» у шапці. Сервери вже запущені локально (3000/8000),
// у CI піднімаються через webServer нижче.
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  outputDir: "test-results",
  use: {
    baseURL: "http://localhost:3000",
    locale: "uk-UA",
    viewport: { width: 1440, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],
  webServer: [
    {
      url: "http://localhost:3000",
      reuseExistingServer: true,
      timeout: 120_000,
      command: "npm.cmd run dev",
    },
  ],
});
