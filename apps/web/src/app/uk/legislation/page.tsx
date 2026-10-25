"use client";

import { useState, useEffect } from "react";
import { listDocuments } from "@/lib/api";
import Link from "next/link";



export default function SearchPage() {
  const [sq, setSq] = useState("");
  const [items, setItems] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    const t = setTimeout(async () => {
      try {
        const r = await listDocuments(sq, 50, 0);
        if (!alive) return;
        setItems(r.items || []);
        setTotal(r.total || 0);
        setError(null);
      } catch (e: any) {
        if (alive) setError(e?.message || "Помилка завантаження");
      } finally {
        if (alive) setLoading(false);
      }
    }, 300);
    return () => { alive = false; clearTimeout(t); };
  }, [sq]);

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
        <div style={{ marginTop: 12 }} className="tag">
          {loading ? "Завантаження…" : `Знайдено: ${total}`}
        </div>
        {error && <p className="text-sm text-red-400" style={{ marginTop: 8 }}>{error}</p>}
        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 8 }}>
          {items.map((d) => (
            <Link key={d.id} href={`/uk/legislation/${d.id}`} className="lvl" style={{ textDecoration: "none" }}>
              <span>{d.title}</span>
              <span className="tag">{d.document_type} · {d.current_known_status || "—"}</span>
            </Link>
          ))}
          {!loading && items.length === 0 && (
            <span className="tag">Нічого не знайдено. Спробуйте інший запит.</span>
          )}
        </div>
      </div>
    </>
  );
}
