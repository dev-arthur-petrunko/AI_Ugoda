"use client";

import InteractiveScene from "@/components/InteractiveScene";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getStats } from "@/lib/api";

const REV = [
  ["01.03.2023", "Платник зобов'язаний подати <del>звіт</del> у строк <del>20</del> днів."],
  ["15.09.2023", "Платник зобов'язаний подати <ins>декларацію</ins> у строк <del>20</del> днів."],
  ["01.01.2024", "Платник зобов'язаний подати декларацію у строк <ins>30</ins> днів."],
  ["Сьогодні", "Платник зобов'язаний подати декларацію у строк 30 днів<ins>, а за порушення сплачує штраф</ins>."],
];

const LV = [
  "Конституція України",
  "Міжнародні договори (ратифіковані)",
  "Закони та кодекси",
  "Постанови Верховної Ради",
  "Укази Президента",
  "Постанови Кабінету Міністрів",
  "Накази міністерств",
  "Акти місцевих органів",
];

const MARK = `<svg class="mark" viewBox="0 0 120 120"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#8F6F2B"/><stop offset=".5" stop-color="#E8C871"/><stop offset="1" stop-color="#A67C2E"/></linearGradient></defs><path class="u" pathLength="1" d="M30 24V62a30 30 0 0 0 60 0V24" fill="none" stroke="url(#g)" stroke-width="7" stroke-linecap="round"/><circle class="pt p1" cx="30" cy="22" r="6.5" fill="url(#g)"/><circle class="pt p2" cx="90" cy="22" r="6.5" fill="url(#g)"/><path class="pt sl" d="M60 86l8 8-8 8-8-8z" fill="url(#g)"/></svg>`;

export default function OverviewPage() {
  const router = useRouter();
  const [sl, setSl] = useState(3);
  const [stats, setStats] = useState<{ documents: number; revisions: number; provisions: number; links: number } | null>(null);
  useEffect(() => { getStats().then(setStats).catch(() => {}); }, []);
  const r = REV[sl];

  const ladder = LV.map((n, i) => {
    const hi = i === 2;
    const lo = i === 6;
    return (
      <div key={i} className={`lvl ${hi ? "hi" : lo ? "lo" : ""}`}>
        <span>{n}</span>
        <span className="tag">{hi ? "перемагає" : lo ? "поступається" : ""}</span>
      </div>
    );
  });

  return (
    <>
      <div className="glass gold hero">
        <div>
          <h1>Законодавство, яке видно наскрізь</h1>
          <p className="lead">
            Закон на будь-яку дату, колізії між нормами і ризики простою мовою. Кожне твердження має посилання на статтю.
          </p>
          <div className="row">
            <button className="btn p" onClick={() => router.push("/uk/legislation")}>Знайти статтю</button>
            <button className="btn s" onClick={() => router.push("/uk/conflicts")}>Хто кого перебиває</button>
          </div>
        </div>
        <InteractiveScene className="hero-scene" height="460px" />
      </div>

      <div className="grid">
        <div className="glass card">
          <h2>Закон на дату</h2>
          <p className="sm">Перетягніть повзунок: зміни підсвічуються. Приклад інтерфейсу, не реальний текст закону.</p>
          <div className="law" dangerouslySetInnerHTML={{ __html: "Стаття N. " + r[1] }} />
          <div className="meta">Редакція від {r[0]}</div>
          <input type="range" min={0} max={3} value={sl} onChange={(e) => setSl(Number(e.target.value))} aria-label="Редакція" />
          <div className="ticks">
            <span>2023</span>
            <span>2023</span>
            <span>2024</span>
            <span>сьогодні</span>
          </div>
        </div>
        <div className="glass card">
          <h2>Хто кого перебиває</h2>
          <p className="sm">Вища юридична сила перемагає. Приклад пари норм.</p>
          {ladder}
          <div className="why">Правило: вища сила. Закон перебиває наказ міністерства, тому наказ у цій частині не застосовується.</div>
        </div>
        <div className="glass card">
          <h2>Стан даних</h2>
          <p className="sm">Чесний статус без вигаданих цифр.</p>
          <div className="st">
            <span>data.rada.gov.ua</span>
            <span>очікує перевірки</span>
          </div>
          <div className="st">
            <span>zakon.rada.gov.ua</span>
            <span>очікує перевірки</span>
          </div>
          <div className="st">
            <span>Імпортовано актів</span>
            <span>{stats ? `${stats.documents} актів · ${stats.revisions} редакцій · ${stats.provisions} статей` : "завантаження…"}</span>
          </div>
          <div className="st">
            <span>Колізій виявлено</span>
            <span>немає даних</span>
          </div>
          <div className="row">
            <button className="btn s" onClick={() => alert("Реальний імпорт запускається в панелі адміністратора після перевірки джерел.")}>
              Як запустити імпорт
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
