import { expect, test } from "@playwright/test";

const API_BASE_URL = process.env.E2E_API_URL ?? "http://localhost:8000";

test("landing page renders", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Camerino",
  );
});

test("api health endpoint responds", async ({ request }) => {
  const response = await request.get(`${API_BASE_URL}/health`);
  expect(response.ok()).toBe(true);
  expect(await response.json()).toEqual({ status: "ok" });
});
