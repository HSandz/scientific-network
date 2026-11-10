import { defineConfig } from "@playwright/test";
// Pure deterministic contracts require neither a browser nor Neo4j/artifact services.
export default defineConfig({
  testDir: "./tests",
  testMatch: "contracts.spec.ts",
  workers: 1,
  forbidOnly: !!process.env.CI,
  reporter: "list",
});
