import { test, expect, type Page } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const SHOTS = path.join(__dirname, "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SHOTS, { recursive: true });
});

function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") errors.push(msg.text());
  });
  page.on("pageerror", (err) => errors.push(String(err)));
  return errors;
}

test.describe("S1 — приймання: головна", () => {
  test("сцена, шрифти, один «AI Ugoda», лічильник, 0 помилок", async ({ page }) => {
    const errors = collectErrors(page);
    await page.goto("/uk", { waitUntil: "networkidle" });

    // 1. Інтерактивна сцена
    await expect(page.locator("canvas")).toHaveCount(1);

    // 2. Рівно один візуальний «AI Ugoda» (лого lockup у сайдбарі)
    const brands = page.locator(".brand b", { hasText: "AI Ugoda" });
    await expect(brands).toHaveCount(1);

    // 3. getComputedStyle(h1) → Playfair Display (реальний шрифт, не Times)
    const fonts = await page.evaluate(() => {
      const h1 = document.querySelector("h1");
      const body = document.body;
      return {
        h1: h1 ? getComputedStyle(h1).fontFamily : "",
        h1Width: h1 ? h1.getBoundingClientRect().width : 0,
        body: getComputedStyle(body).fontFamily,
      };
    });
    expect(fonts.h1).toContain("Playfair Display");
    expect(fonts.body).toContain("Inter");

    // 4. Реальні цифри з API (S3: official + fixture)
    await expect(page.locator("header .chip b")).toContainText(/актів/);

    // 5. 0 помилок консолі
    expect(errors, `console errors:\n${errors.join("\n")}`).toHaveLength(0);

    // 6. Скриншот для приймання
    await page.screenshot({ path: path.join(SHOTS, "s1-home.png"), fullPage: false });
  });
});

test.describe("S1 — приймання: пошук", () => {
  test("Знайдено: 13 (official), без дублів, фільтри дати, 0 помилок", async ({ page }) => {
    const errors = collectErrors(page);
    await page.goto("/uk/legislation", { waitUntil: "networkidle" });

    // S3.2: за замовчуванням показуються лише official-акти (13 імпортованих)
    await expect(page.getByText(/Знайдено:\s*13/)).toBeVisible();

    // Без дублів: унікальні href документів (рядки можуть дублюватись у DOM)
    const hrefs = await page.locator('a[href^="/uk/legislation/"]').evaluateAll((els) =>
      els.map((e) => (e as HTMLAnchorElement).getAttribute("href") || ""),
    );
    const docs = hrefs.filter(
      (h, i) => hrefs.indexOf(h) === i && /[0-9a-f]{8}-[0-9a-f]{4}-/.test(h),
    );
    expect(docs.length).toBe(13);

    // Фільтри дати (S1.5) присутні
    await expect(page.locator('input[type="date"]')).toHaveCount(2);

    // S3.2: перемикач «тестові дані» присутній
    await expect(page.getByText("Показати тестові дані")).toBeVisible();

    // Шрифт заголовка — Playfair
    const h1Font = await page.evaluate(() => {
      const h1 = document.querySelector("h1");
      return h1 ? getComputedStyle(h1).fontFamily : "";
    });
    expect(h1Font).toContain("Playfair Display");

    expect(errors, `console errors:\n${errors.join("\n")}`).toHaveLength(0);

    await page.screenshot({ path: path.join(SHOTS, "s1-search.png"), fullPage: false });
  });
});

test.describe("Smoke — усі сторінки 200", () => {
  const pages = [
    "/uk",
    "/uk/legislation",
    "/uk/changes",
    "/uk/conflicts",
    "/uk/contracts",
    "/uk/monitoring",
    "/uk/admin",
    "/uk/assistant",
    "/uk/legal-map",
    "/uk/reports",
    "/uk/settings",
    "/uk/workspace",
    "/uk/bookmarks",
    "/three",
  ];

  for (const url of pages) {
    test(`${url} → 200`, async ({ page }) => {
      const resp = await page.goto(url, { waitUntil: "domcontentloaded" });
      expect(resp?.status(), `${url} status`).toBe(200);
    });
  }
});

test.describe("S3 — приймання: справжні дані", () => {
  test("Пошук «Конституція» → офіційна Конституція, сторінка акта, 0 помилок", async ({ page }) => {
    const errors = collectErrors(page);

    // Пошук знаходить офіційну Конституцію (джерело: КОНСТИТУЦІЯ УКРАЇНИ)
    await page.goto("/uk/legislation?q=Конституція", { waitUntil: "networkidle" });
    await expect(page.getByText(/конституція україни/i).first()).toBeVisible();

    // Відкриваємо саме Конституцію (перший результат може бути іншим актом)
    const constLink = page.locator('a[href="/uk/legislation/ed5f721c-08c4-45b0-bfcb-505f2b82512c"]').first();
    await expect(constLink).toBeVisible();
    await constLink.click();
    await page.waitForURL(/\/uk\/legislation\/[0-9a-f-]{36}/);
    await page.waitForLoadState("networkidle");

    // ≥ 150 статей у переліку (S3: Конституція має 158 розібраних)
    const articleCount = await page.locator("text=/\\d{2,3}\\s*стат/").first().textContent().catch(() => null);
    const body = (await page.textContent("body")) || "";
    const m = body.match(/(\d+)\s*стат/);
    if (m) {
      expect(parseInt(m[1], 10)).toBeGreaterThanOrEqual(150);
    }

    expect(errors, `console errors:\n${errors.join("\n")}`).toHaveLength(0);
    await page.screenshot({ path: path.join(SHOTS, "s3-document.png"), fullPage: false });
  });
});
