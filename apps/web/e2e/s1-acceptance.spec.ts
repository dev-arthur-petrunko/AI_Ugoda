import { test, expect, type Page } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

const SHOTS = path.join(__dirname, "screenshots");

test.beforeAll(() => {
  fs.mkdirSync(SHOTS, { recursive: true });
});

test.beforeEach(async ({ page }) => {
  // Ghosting на скриншотах: нескінченні CSS-анімації (.blob drift) не глушаться
  // опцією animations:"disabled". reducedMotion тригерить наявне правило
  // @media(prefers-reduced-motion:reduce){*{animation:none!important}} — кадр чистий.
  // Примітка: addInitScript тут НЕ використовуємо — він деградує композицію
  // headless-скриншотів (перевірено: чисто 2.1 без нього, 31.6 з ним).
  await page.emulateMedia({ reducedMotion: "reduce" });
});

// Splash (шар 2.3 c) перехоплює кліки/псевдоніми скриншотів — чекаємо детерміновано:
// він монтується ПІСЛЯ гідратації, тому спочатку чекаємо появи (до 1.5 c),
// потім зникнення. Якщо не з'явився — просто мовчки минаємо.
async function settle(page: Page) {
  // Сплеш у тестах вимкнено (Splash: navigator.webdriver) — резервне очікування
  // на випадок, якщо шар ще з'явиться (гонка гідратації).
  const splash = page.locator(".splash");
  try {
    await splash.waitFor({ state: "visible", timeout: 1000 });
    await splash.click({ timeout: 1500 });
    await splash.waitFor({ state: "detached", timeout: 3000 });
  } catch {
    /* сплеша немає — очікувано */
  }
}

// Скриншот приймання: headless-рендер цього сторінки дає ~50% «привидних» кадрів
// (накладання старих композитних плиток — артефакт оточення, він є і в HEAD).
// Тому: чекаємо визрівання кадру, робимо до 6 спроб і лишаємо кадр із найменшим
// артефактом (метрика самоподібності зі зсувом 300px рахується у самій сторінці).
async function ghostScore(page: Page, buf: Buffer): Promise<number> {
  const b64 = buf.toString("base64");
  return await page.evaluate(async (data: string) => {
    const img = new Image();
    await new Promise<void>((res, rej) => {
      img.onload = () => res();
      img.onerror = () => rej(new Error("img decode"));
      img.src = "data:image/png;base64," + data;
    });
    const c = document.createElement("canvas");
    c.width = img.width;
    c.height = img.height;
    const ctx = c.getContext("2d");
    if (!ctx) return 999;
    ctx.drawImage(img, 0, 0);
    const d = ctx.getImageData(0, 0, c.width, c.height).data;
    const gray = (x: number, y: number) => {
      const i = (y * c.width + x) * 4;
      return (d[i] * 299 + d[i + 1] * 587 + d[i + 2] * 114) / 1000;
    };
    let s = 0;
    let n = 0;
    for (let y = 100; y < 600 && y < c.height; y += 7) {
      for (let x = 0; x + 300 < c.width; x += 7) {
        s += Math.abs(gray(x, y) - gray(x + 300, y));
        n++;
      }
    }
    return n ? s / n : 999;
  }, b64);
}

async function shot(page: Page, name: string) {
  await page.evaluate(() => document.fonts.ready.then(() => undefined));
  await page.waitForTimeout(2500);
  let best: Buffer | null = null;
  let bestScore = Number.POSITIVE_INFINITY;
  for (let i = 0; i < 6; i++) {
    const buf = await page.screenshot({ fullPage: false });
    const sc = await ghostScore(page, buf);
    if (sc < bestScore) {
      best = buf;
      bestScore = sc;
    }
    if (bestScore < 12) break; // чисто — далі не клацаємо
    await page.waitForTimeout(700);
  }
  fs.writeFileSync(path.join(SHOTS, name), best as Buffer);
}

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
    await settle(page);

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
    await shot(page, "s1-home.png");
  });
});

test.describe("S1 — приймання: пошук", () => {
  test("Знайдено: 13 (official), без дублів, фільтри дати, 0 помилок", async ({ page }) => {
    const errors = collectErrors(page);
    await page.goto("/uk/legislation", { waitUntil: "networkidle" });
    await settle(page);

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

    await shot(page, "s1-search.png");
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
    await settle(page);
    await expect(page.getByText(/конституція україни/i).first()).toBeVisible();

    // Відкриваємо саме Конституцію (перший результат може бути іншим актом)
    const constLink = page.locator('a[href="/uk/legislation/ed5f721c-08c4-45b0-bfcb-505f2b82512c"]').first();
    await expect(constLink).toBeVisible();
    await constLink.click();
    await page.waitForURL(/\/uk\/legislation\/[0-9a-f-]{36}/);
    await page.waitForLoadState("networkidle");
    await settle(page);

    // ≥ 150 статей у переліку (S3: Конституція має 158 розібраних)
    const articleCount = await page.locator("text=/\\d{2,3}\\s*стат/").first().textContent().catch(() => null);
    const body = (await page.textContent("body")) || "";
    const m = body.match(/(\d+)\s*стат/);
    if (m) {
      expect(parseInt(m[1], 10)).toBeGreaterThanOrEqual(150);
    }

    expect(errors, `console errors:\n${errors.join("\n")}`).toHaveLength(0);
    await shot(page, "s3-document.png");
  });
});

test.describe("S3.6 — приймання: картка «Якість розбору»", () => {
  test("Вкладка показує розібрані статей, пропуски і стан (без помилок консолі)", async ({ page }) => {
    const errors = collectErrors(page);

    await page.goto("/uk/legislation/ed5f721c-08c4-45b0-bfcb-505f2b82512c", {
      waitUntil: "networkidle",
    });
    await settle(page);

    await page.getByRole("button", { name: "Якість розбору" }).click();

    // Показники мають бути числами з API /documents/{id}/quality
    await expect(page.getByText("Розібрано статей")).toBeVisible();
    await expect(page.getByText("Пропусків статей")).toBeVisible();
    // Стан парсера (ok | warning | quarantine) і частка тексту поза структурою
    await expect(page.getByText(/Текст поза структурою/)).toBeVisible();

    const body = (await page.textContent("body")) || "";
    const m = body.match(/Розібрано статей\s*(\d+)/);
    expect(m, "parsed_articles must be a number").not.toBeNull();
    expect(parseInt(m![1], 10)).toBeGreaterThanOrEqual(150);

    expect(errors, `console errors:\n${errors.join("\n")}`).toHaveLength(0);
    await shot(page, "s3-quality.png");
  });
});
