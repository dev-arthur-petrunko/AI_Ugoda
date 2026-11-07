"use client";

import InteractiveScene from "@/components/InteractiveScene";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getStats, listDocuments } from "@/lib/api";
import {
  Scale,
  GitCompareArrows,
  BellRing,
  Bookmark,
  BarChart3,
  FolderOpen,
  Search,
  ArrowRight,
} from "lucide-react";

type Stats = {
  documents: number;
  revisions: number;
  provisions: number;
  links: number;
  documents_official?: number;
  documents_fixture?: number;
};

type Doc = {
  id: string;
  title: string;
  document_type: string | null;
  current_known_status: string | null;
  data_origin?: string;
};

const ACTIONS = [
  {
    href: "/uk/assistant",
    icon: Scale,
    title: "AI Юрист-дослідник",
    desc: "Питання з цитуванням статей із бази",
  },
  {
    href: "/uk/conflicts",
    icon: GitCompareArrows,
    title: "Протиріччя та колізії",
    desc: "Хто кого перебиває: юридична сила норм",
  },
  {
    href: "/uk/monitoring",
    icon: BellRing,
    title: "Моніторинг",
    desc: "Слідкувати за змінами актів і статей",
  },
  {
    href: "/uk/bookmarks",
    icon: Bookmark,
    title: "Закладки",
    desc: "Збережені акти та положення",
  },
  {
    href: "/uk/reports",
    icon: BarChart3,
    title: "Звіти",
    desc: "Показники бази законодавства",
  },
  {
    href: "/uk/workspace",
    icon: FolderOpen,
    title: "Мої документи",
    desc: "Приватне сховище завантажених файлів",
  },
];

export default function OverviewPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [statsErr, setStatsErr] = useState(false);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [docsErr, setDocsErr] = useState(false);
  const [q, setQ] = useState("");

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
    listDocuments("", 8, 0)
      .then((r) => {
        if (alive) {
          setDocs(r.items || []);
          setDocsErr(false);
        }
      })
      .catch(() => {
        if (alive) setDocsErr(true);
      });
    return () => {
      alive = false;
    };
  }, []);

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = q.trim();
    router.push(query ? `/uk/legislation?q=${encodeURIComponent(query)}` : "/uk/legislation");
  };

  return (
    <>
      <div className="glass gold hero">
        <div>
          <h1>Законодавство, яке видно наскрізь</h1>
          <p className="lead">
            Закон на будь-яку дату, колізії між нормами і ризики простою мовою. Кожне твердження має
            посилання на статтю.
          </p>
          <form className="row" onSubmit={submitSearch}>
            <input
              className="field"
              style={{ maxWidth: 360 }}
              placeholder="Наприклад: податковий кодекс, строк позовної давності…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="Пошук законодавства"
            />
            <button className="btn p" type="submit">
              <Search className="h-4 w-4" style={{ marginRight: 6, verticalAlign: -2 }} />
              Знайти статтю
            </button>
          </form>
        </div>
        <InteractiveScene className="hero-scene" height="460px" />
      </div>

      {/* Швидкі дії */}
      <div className="grid">
        {ACTIONS.map((a) => (
          <Link key={a.href} href={a.href} className="glass card" style={{ textDecoration: "none", color: "inherit" }}>
            <div className="flex items-center gap-2 mb-1">
              <a.icon className="h-4 w-4" />
              <h2 style={{ margin: 0 }}>{a.title}</h2>
            </div>
            <p className="sm" style={{ margin: 0 }}>{a.desc}</p>
          </Link>
        ))}
      </div>

      {/* Реальні акти з бази */}
      <div className="glass card" style={{ marginTop: 20 }}>
        <div className="flex items-center justify-between gap-2">
          <h2 style={{ margin: 0 }}>Акти в базі</h2>
          <Link href="/uk/legislation" className="btn s">
            Усі акти <ArrowRight className="h-4 w-4" style={{ marginLeft: 4, verticalAlign: -2 }} />
          </Link>
        </div>
        <p className="sm">
          {stats
            ? `Офіційних: ${stats.documents_official ?? 0} · тестових: ${stats.documents_fixture ?? 0} · статей: ${stats.provisions}`
            : statsErr
              ? "Помилка завантаження (API недоступний)"
              : "Завантаження…"}
        </p>
        {docsErr && <p className="tag">Не вдалося завантажити перелік актів.</p>}
        <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
          {!docsErr &&
            docs.map((d) => (
              <Link
                key={d.id}
                href={`/uk/legislation/${d.id}`}
                className="lvl"
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <span>{d.title}</span>
                <span className="tag">
                  {d.document_type || "Акт"} · {d.current_known_status || "—"}
                  {d.data_origin === "fixture" && (
                    <span style={{ marginLeft: 8, padding: "1px 6px", borderRadius: 6, background: "rgba(255,196,0,.15)", color: "#d9a400", fontSize: 11 }}>
                      тестові дані
                    </span>
                  )}
                </span>
              </Link>
            ))}
          {!docsErr && docs.length === 0 && (
            <span className="tag">Актів ще не імпортовано.</span>
          )}
        </div>
      </div>

      {/* Стан системи */}
      <div className="glass card" style={{ marginTop: 20 }}>
        <h2>Стан даних</h2>
        <p className="sm">Чесний статус без вигаданих цифр.</p>
        <div className="st">
          <span>Актів · редакцій · статей</span>
          <span>
            {stats
              ? `${stats.documents} · ${stats.revisions} · ${stats.provisions}`
              : statsErr
                ? "помилка завантаження"
                : "завантаження…"}
          </span>
        </div>
        <div className="st">
          <span>Походження даних</span>
          <span>
            {stats
              ? `офіційних: ${stats.documents_official ?? 0} · тестових: ${stats.documents_fixture ?? 0}`
              : statsErr
                ? "помилка завантаження"
                : "завантаження…"}
          </span>
        </div>
        <div className="st">
          <span>Джерело текстів</span>
          <span>zakon.rada.gov.ua (білий список)</span>
        </div>
        <div className="st">
          <span>Колізій виявлено</span>
          <span>{stats ? (stats.links ?? 0) : "—"}</span>
        </div>
        <div className="row">
          <Link href="/uk/admin" className="btn s">
            Панель адміністратора
          </Link>
          <Link href="/uk/changes" className="btn s">
            Нові закони та зміни
          </Link>
        </div>
      </div>
    </>
  );
}
