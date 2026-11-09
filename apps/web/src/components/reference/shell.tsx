"use client";

import { usePathname, useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { getStats } from "@/lib/api";
import { readTheme, applyTheme, type Theme } from "@/lib/theme";
import { useEffect, useState } from "react";

const NAV = [
  ["overview", "Огляд", "/uk"],
  ["search", "Пошук законодавства", "/uk/legislation"],
  ["news", "Нові закони та зміни", "/uk/changes"],
  ["ask", "AI Юрист-дослідник", "/uk/assistant"],
  ["conflicts", "Протиріччя та колізії", "/uk/conflicts"],
  ["map", "Карта законодавства", "/uk/legal-map"],
  ["watch", "Моніторинг", "/uk/monitoring"],
  ["docs", "Мої документи", "/uk/workspace"],
  ["bookmarks", "Закладки", "/uk/bookmarks"],
  ["reports", "Звіти", "/uk/reports"],
  ["contracts", "Аналіз договорів", "/uk/contracts"],
  ["settings", "Налаштування", "/uk/settings"],
  ["admin", "Панель адміністратора", "/uk/admin"],
  ["rada", "Верховна Рада", "https://zakon.rada.gov.ua"],
];

// S3 (v5 §5.5): сайдбар — рівно 8 пунктів; решта (bookmarks, reports, contracts,
// settings, admin) лишаються у NAV: доступні через Ctrl+K пошук і швидкі дії
// на головній. NAV_PERSONAL/NAV_ADMIN не прибираємо зі сторінок — лише з меню.
const NAV_MAIN = NAV.slice(0, 8);
export const NAV_ALL = NAV;

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [sideOpen, setSideOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [q, setQ] = useState("");
  const [toast, setToast] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>("dark");
  const [stats, setStats] = useState<{ documents: number; revisions: number; provisions: number; links: number } | null>(null);
  const [statsErr, setStatsErr] = useState(false);

  useEffect(() => {
    let alive = true;
    getStats()
      .then((s) => {
        if (alive) {
          setStats(s);
          setStatsErr(false);
        }
      })
      .catch(() => {
        if (alive) setStatsErr(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setModalOpen(true);
      }
      if (e.key === "Escape") setModalOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3800);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    setTheme(readTheme());
  }, []);

  const activeId = (() => {
    if (pathname === "/uk/admin") return "admin";
    if (pathname === "/uk/legislation" || pathname.startsWith("/uk/legislation/")) return "search";
    if (pathname === "/uk/changes") return "news";
    if (pathname === "/uk/contracts") return "contracts";
    if (pathname === "/uk/assistant") return "ask";
    if (pathname === "/uk/conflicts") return "conflicts";
    if (pathname === "/uk/legal-map") return "map";
    if (pathname === "/uk/monitoring") return "watch";
    if (pathname === "/uk/workspace") return "docs";
    if (pathname === "/uk/bookmarks") return "bookmarks";
    if (pathname === "/uk/reports") return "reports";
    if (pathname === "/uk/settings") return "settings";
    return "overview";
  })();

  const go = (href: string) => {
    if (/^https?:\/\//.test(href)) {
      window.open(href, "_blank", "noopener,noreferrer");
    } else {
      router.push(href);
    }
    setSideOpen(false);
    setModalOpen(false);
  };

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    applyTheme(next);
    setTheme(next);
  };

  const filtered = NAV.filter(([, label]) => label.toLowerCase().includes(q.toLowerCase()));

  return (
    <>
      <div className="blob b1" />
      <div className="blob b2" />
      <div className="noise" />
      <div className="app">
        <aside className={`side glass ${sideOpen ? "open" : ""}`}>
          <div className="brand">
            <Logo variant="lockup" size={34} />
          </div>
          <div id="nav">
            <div className="grp">Розділи</div>
            {NAV_MAIN.map(([id, label, href]) => (
              <button
                key={id}
                className="nav"
                data-go={id}
                aria-current={activeId === id ? "page" : "false"}
                onClick={() => go(href)}
              >
                <span className="dot" />
                {label}
              </button>
            ))}
            <div className="grp">Джерела та тема</div>
            <a
              className="nav"
              data-go="rada"
              href="https://zakon.rada.gov.ua"
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => setSideOpen(false)}
            >
              <span className="dot" />
              Верховна Рада
            </a>
            <button
              className="nav"
              data-go="theme"
              aria-pressed={theme === "light"}
              onClick={toggleTheme}
            >
              <span className="dot" />
              {theme === "dark" ? "☀ Світла тема" : "🌙 Нічна тема"}
            </button>
          </div>
        </aside>
        <div className="main">
          <header className="top glass">
            <button className="nav menu" style={{ width: "auto" }} onClick={() => setSideOpen((v) => !v)} aria-label="Меню">
              <span className="dot" />
            </button>
            <button className="search" onClick={() => setModalOpen(true)}>
              Пошук законодавства, статті або питання
              <kbd>Ctrl K</kbd>
            </button>
            <div className="chip">
              Актів у БД
              <br />
              <b>{stats ? `${stats.documents} актів · ${stats.provisions} статей` : statsErr ? "немає зв'язку з API" : "завантаження…"}</b>
            </div>
          </header>
          <section className="view" tabIndex={-1}>
            {children}
            <footer className="site-footer" role="contentinfo">
              <p className="disclaimer">
                Незалежний сервіс. Не пов'язаний з Верховною Радою України. Дані взято з офіційних
                відкритих джерел.
              </p>
              <p className="attribution">Дані: Верховна Рада України, zakon.rada.gov.ua</p>
            </footer>
          </section>
        </div>
      </div>
      <div className={`modal ${modalOpen ? "on" : ""}`} onClick={(e) => { if (e.target === e.currentTarget) setModalOpen(false); }}>
        <div className="pal glass">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Куди перейти або що знайти?"
            autoFocus={modalOpen}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                const first = filtered[0];
                if (first) go(first[2]);
              }
            }}
          />
          <div>
            {filtered.map(([id, label, href]) => (
              <button
                key={id}
                className="nav"
                style={{ width: "100%" }}
                onClick={() => go(href)}
              >
                <span className="dot" />
                {label}
              </button>
            ))}
            {filtered.length === 0 && <p className="tag" style={{ padding: 12 }}>Нічого не знайдено. Спробуйте назву розділу.</p>}
          </div>
        </div>
      </div>
      {toast && (
        <div className="toast glass gold on" role="status">
          {toast}
        </div>
      )}
    </>
  );
}
