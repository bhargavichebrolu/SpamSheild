import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";

/**
 * Browser tests run against the real backend and the real frozen model, with nothing stubbed.
 * The API-down run starts only the website, to test what happens with no backend.
 */
const apiDown = Boolean(process.env.E2E_API_DOWN);
const python = process.env.E2E_PYTHON ?? resolve("../.venv/Scripts/python.exe");

export default defineConfig({
  testDir: "tests/e2e",
  testMatch: apiDown ? "api-down.spec.ts" : "app.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    // Uses the Edge browser already on this computer, so nothing extra is downloaded.
    channel: process.env.E2E_BROWSER_CHANNEL ?? "msedge",
    screenshot: "only-on-failure",
  },
  webServer: [
    ...(apiDown
      ? []
      : [
          {
            command: `"${python}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
            cwd: "../backend",
            url: "http://127.0.0.1:8000/api/health",
            reuseExistingServer: false,
            timeout: 60_000,
          },
        ]),
    {
      command: "npm run dev",
      url: "http://localhost:5173",
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
