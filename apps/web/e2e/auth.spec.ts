import { test, expect } from "@playwright/test";

// S1.5: вхід зберігає JWT у localStorage → /api/v1/bookmarks із токеном відповідає 200.
test.describe("S1.5 — вхід (JWT)", () => {
  test("реєстрація + вхід → токен у localStorage, закладки без 401", async ({ page, request }) => {
    const email = `e2e-${Date.now()}@example.com`;
    const password = "secret123";

    await page.goto("/uk/settings", { waitUntil: "networkidle" });

    await page.getByPlaceholder("Електронна пошта").fill(email);
    await page.getByPlaceholder("Пароль").fill(password);
    await page.getByRole("button", { name: "Зареєструватися" }).click();

    await expect(page.getByText("Реєстрацію завершено.")).toBeVisible();

    const token = await page.evaluate(() => localStorage.getItem("aiugoda_token"));
    expect(token, "токен має зберігатися в localStorage").toBeTruthy();

    // Захищений ендпоінт із токеном → 200 (без токена вимагав би 401)
    const authed = await request.get("/api/v1/bookmarks", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(authed.status()).toBe(200);

    // Скидання сесії → токена немає
    await page.getByRole("button", { name: "Вийти" }).click();
    const after = await page.evaluate(() => localStorage.getItem("aiugoda_token"));
    expect(after).toBeNull();
  });
});
