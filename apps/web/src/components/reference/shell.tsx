"use client";

import { usePathname, useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { getStats } from "@/lib/api";
import { useEffect, useState } from "react";

const NAV = [
  ["overview", "Огляд", "/uk"],
  ["search", "Пошук законодавства", "/uk/legislation"],
  ["news", "Нові закони та зміни", "/uk/changes"],
  ["contracts", "Аналіз договорів", "/uk/contracts"],
  ["ask", "AI Юрист-дослідник", "/uk"],
  ["conflicts", "Протиріччя та колізії", "/uk/conflicts"],
  ["map", "Карта законодавства", "/uk"],
  ["watch", "Моніторинг", "/uk"],
  ["docs", "Мої документи", "/uk"],
  ["reports", "Звіти", "/uk"],
  ["settings", "Налаштування", "/uk"],
  ["admin", "Панель адміністратора", "/uk/admin"],
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [sideOpen, setSideOpen] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [q, setQ] = useState("");
  const [toast, setToast] = useState<string | null>(null);
  const [stats, setStats] = useState<{ documents: number; revisions: number; provisions: number; links: number } | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch(() => {});
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

  const activeId = (() => {
    if (pathname === "/uk/admin") return "admin";
    if (pathname === "/uk/legislation") return "search";
    if (pathname === "/uk/changes") return "news";
    if (pathname === "/uk/contracts") return "contracts";
    if (pathname === "/uk/conflicts") return "conflicts";
    return "overview";
  })();

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
            <b>
              <i>AI</i> Ugoda
            </b>
          </div>
          <div id="nav">
            <div className="grp">Розділи</div>
            {NAV.map(([id, label, href], i) => (
              <span key={id}>
                {i === 11 && <div className="grp">Адміністрування</div>}
                <button
                  className="nav"
                  data-go={id}
                  aria-current={activeId === id ? "page" : "false"}
                  onClick={() => {
                    router.push(href);
                    setSideOpen(false);
                  }}
                >
                  <span className="dot" />
                  {label}
                </button>
              </span>
            ))}
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
              <b>{stats ? `${stats.documents} актів · ${stats.provisions} статей` : "завантаження…"}</b>
            </div>
          </header>
          <section className="view" tabIndex={-1}>
            {children}
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
                if (first) {
                  router.push(first[2]);
                  setModalOpen(false);
                }
              }
            }}
          />
          <div>
            {filtered.map(([id, label, href]) => (
              <button
                key={id}
                className="nav"
                style={{ width: "100%" }}
                onClick={() => {
                  router.push(href);
                  setModalOpen(false);
                }}
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
