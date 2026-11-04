"use client";

import { useState, useEffect } from "react";
import { listDocuments } from "@/lib/api";
import Link from "next/link";



export default function SearchPage() {
  const [sq, setSq] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryTick, setRetryTick] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await listDocuments(sq, 50, 0, dateFrom, dateTo);
        if (!alive) return;
        setItems(r.items || []);
        setTotal(r.total || 0);
        setError(null);
      } catch (e: any) {
        if (alive) {
          setItems([]);
          setTotal(0);
          setError(e?.message || "Помилка завантаження");
        }
      } finally {
        if (alive) setLoading(false);
      }
    }, 300);
    return () => { alive = false; clearTimeout(t); };
  }, [sq, dateFrom, dateTo, retryTick]);

  return (
    <>
      <h1 style={{ maxWidth: "20ch" }}>Знайти закон або статтю</h1>
      <div className="glass card" style={{ marginTop: 22 }}>
        <input
          className="field"
          id="sq"
          placeholder="Наприклад: податковий кодекс, декларація, строк подання"
          value={sq}
          onChange={(e) => setSq(e.target.value)}
          autoFocus
        />
        <div style={{ marginTop: 12, display: "flex", gap: 12, flexWrap: "wrap" }}>
          <label className="tag" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            Прийнято від
            <input
              type="date"
              className="field"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              style={{ minWidth: 150 }}
            />
          </label>
          <label className="tag" style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            Прийнято до
            <input
              type="date"
              className="field"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              style={{ minWidth: 150 }}
            />
          </label>
          {(dateFrom || dateTo) && (
            <button
              className="btn s"
              style={{ alignSelf: "flex-end" }}
              onClick={() => {
                setDateFrom("");
                setDateTo("");
              }}
            >
              Скинути дати
            </button>
          )}
        </div>
        <div style={{ marginTop: 12 }} className="tag">
          {loading ? "Завантаження…" : error ? "Помилка" : `Знайдено: ${total}`}
        </div>
        {error && (
          <div style={{ marginTop: 8 }} role="alert">
            <p className="text-sm text-red-400">{error}</p>
            <button className="btn s" style={{ marginTop: 8 }} onClick={() => setRetryTick((n) => n + 1)}>
              Повторити
            </button>
          </div>
        )}
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          {!loading && !error && items.map((d, i) => (
            <Link key={`${d.id}-${i}`} href={`/uk/legislation/${d.id}`} className="lvl" style={{ textDecoration: "none" }}>
              <span>{d.title}</span>
              <span className="tag">{d.document_type} · {d.current_known_status || "—"}</span>
            </Link>
          ))}
          {!loading && !error && items.length === 0 && (
            <span className="tag">Нічого не знайдено. Спробуйте інший запит.</span>
          )}
        </div>
      </div>
    </>
  );
}
