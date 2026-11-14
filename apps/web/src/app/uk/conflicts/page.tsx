"use client";

import { useEffect, useState } from "react";
import { getConflicts } from "@/lib/api";

type Conflict = {
  id: string;
  conflict_type: string;
  confidence: string;
  review_status: string;
  rule_applied: string | null;
  explanation: string | null;
  evidence: Record<string, any>;
  found_by: string;
  reviewed_by: string | null;
};

const TYPE_LABELS: Record<string, string> = {
  HIERARCHY_CONFLICT: "Конфлікт ієрархії (скоро)",
  SPECIAL_VS_GENERAL: "Спеціальна vs загальна (скоро)",
  SAME_LEVEL_NEWER: "Новіша на тому ж рівні (скоро)",
  DEAD_REFERENCE: "Мертвe посилання",
  GHOST_NORM: "Привид-норма (скоро)",
  CODE_DUPLICATION: "Дублювання в кодексі",
  UNCONSTITUTIONAL: "Неконституційність (скоро)",
  EXPIRING: "Тимчасова норма: сплив строку",
  EU_MISMATCH: "Розбіжність з EU (скоро)",
};

const CONF_LABELS: Record<string, string> = {
  high: "висока",
  medium: "середня",
  low: "низька",
};

export default function ConflictsPage() {
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [items, setItems] = useState<Conflict[]>([]);
  const [total, setTotal] = useState(0);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const load = () => {
    setState("loading");
    getConflicts()
      .then((res) => {
        setItems(res.items || []);
        setTotal(res.total ?? (res.items || []).length);
        setState("ready");
      })
      .catch((e: any) => {
        setErrMsg(e?.message || "Немає зв'язку з сервером");
        setState("error");
      });
  };

  useEffect(load, []);

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
  const ladder = LV.map((n, i) => (
    <div key={i} className={`lvl ${i === 2 ? "hi" : i === 6 ? "lo" : ""}`}>
      <span>{n}</span>
      <span className="tag">{i === 2 ? "перемагає" : i === 6 ? "поступається" : ""}</span>
    </div>
  ));
  return (
    <>
      <h1 style={{ maxWidth: "18ch" }}>Протиріччя та колізії</h1>
      <p className="lead">Якщо дві норми суперечать, переможця визначають правила, а не здогадка. Знайдені кандидати — орієнтир, не юридична оцінка; остаточно визначає експерт.</p>
      <div className="grid">
        <div className="glass card">
          <h2>Рівні сили</h2>
          {ladder}
        </div>
        <div className="glass card">
          <h2>Правила вибору</h2>
          <div className="why">Вища сила перемагає нижчу. <span className="tag">(принцип)</span></div>
          <div className="why">Спеціальна норма перемагає загальну. <span className="tag">(скоро)</span></div>
          <div className="why">На одному рівні перемагає новіша. <span className="tag">(скоро)</span></div>
          <div className="why">Рішення Конституційного Суду скасовує норму. <span className="tag">(скоро)</span></div>
        </div>
        <div className="glass card">
          <h2>Знайдені колізії</h2>
          {state === "loading" && <p className="tag">Завантаження…</p>}
          {state === "error" && (
            <div>
              <p className="tag" style={{ color: "#e08a8a" }}>{errMsg}</p>
              <button className="btn s" style={{ marginTop: 10 }} onClick={load}>
                Повторити
              </button>
            </div>
          )}
          {state === "ready" && items.length === 0 && (
            <p className="tag">Кандидатів поки не знайдено. Завантаження й аналіз офіційних текстів триває.</p>
          )}
          {state === "ready" && items.length > 0 && (
            <>
              <p className="tag" style={{ marginBottom: 8 }}>
                Всього кандидатів: {total} · усі очікують на перевірку експерта
              </p>
              <div className="space-y-2">
                {items.map((c, i) => (
                  <div key={c.id || i} className="lvl" style={{ alignItems: "flex-start" }}>
                    <span>
                      <b>{TYPE_LABELS[c.conflict_type] || c.conflict_type}</b>{" "}
                      <span className="tag">
                        знайдено: {c.found_by === "code" ? "програмою (правило)" : c.found_by}
                      </span>
                      <br />
                      <span className="tag">
                        певність: {CONF_LABELS[c.confidence] || c.confidence} (правило)
                        {c.rule_applied ? ` · правило: ${c.rule_applied}` : ""}
                      </span>
                      {c.explanation && <br />}
                      {c.explanation && <span className="tag">{c.explanation}</span>}
                      {c.evidence?.reference_quote && (
                        <>
                          <br />
                          <span className="tag">Цитата: «{c.evidence.reference_quote}»</span>
                        </>
                      )}
                      {c.evidence?.quote && (
                        <>
                          <br />
                          <span className="tag">Цитата: «{String(c.evidence.quote).slice(0, 300)}»</span>
                        </>
                      )}
                      {c.evidence?.excluded_note && (
                        <>
                          <br />
                          <span className="tag">Виключення: {c.evidence.excluded_note}</span>
                        </>
                      )}
                    </span>
                    <span className="tag">
                      {c.review_status}
                      {c.reviewed_by ? ` · ${c.reviewed_by}` : ""}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
