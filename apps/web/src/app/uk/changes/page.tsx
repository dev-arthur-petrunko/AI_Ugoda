"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Clock } from "lucide-react";
import { listDocuments, getSyncStatus, type DocumentItem } from "@/lib/api";
import Link from "next/link";

export default function ChangesPage() {
  const [items, setItems] = useState<DocumentItem[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [errMsg, setErrMsg] = useState<string | null>(null);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  const load = () => {
    setState("loading");
    Promise.all([
      listDocuments("", 10, 0),
      getSyncStatus().catch(() => null),
    ])
      .then(([docs, sync]) => {
        // Фід змін ще не імпортується, показуємо найновіші редакції за датою.
        const sorted = [...(docs.items || [])].sort((a, b) =>
          String(b.revision_date || b.adoption_date || "").localeCompare(
            String(a.revision_date || a.adoption_date || ""),
          ),
        );
        setItems(sorted);
        setSyncNote(sync ? `Джерела: ${(sync.connectors || []).join(", ")}` : null);
        setState("ready");
      })
      .catch((e: any) => {
        setErrMsg(e?.message || "Немає зв'язку з сервером");
        setState("error");
      });
  };

  useEffect(load, []);

  return (
    <PageShell
      title="Нові закони та зміни"
      subtitle="Події законодавства: нові акти, поправки, дати вступу в чинність та втрата чинності."
    >
      <div className="space-y-4">
        {syncNote && <p className="tag">{syncNote}</p>}

        {state === "loading" && <p className="text-text-secondary">Завантаження…</p>}

        {state === "error" && (
          <div className="glass card text-center py-8">
            <p className="text-red-400 text-sm">{errMsg}</p>
            <button className="btn s" style={{ marginTop: 10 }} onClick={load}>
              Повторити
            </button>
          </div>
        )}

        {state === "ready" && items.length === 0 && (
          <EmptyState
            icon={<Clock className="h-5 w-5" />}
            title="Лента змін ще порожня"
            description="Виявлені зміни зʼявляться після імпорту ревізій з zakon.rada.gov.ua. Кожна подія містить посилання на джерело та дату відкриття."
            actionLabel="Перейти на дашборд"
            actionHref="/uk"
          />
        )}

        {state === "ready" && items.length > 0 && (
          <div className="space-y-2">
            {items.map((d) => (
              <Link key={d.id} href={`/uk/legislation/${d.id}`} className="glass card block hover:opacity-90">
                <p className="font-medium">{d.title}</p>
                <p className="tag">
                  {[d.document_type, d.adoption_date, d.current_known_status].filter(Boolean).join(" · ")}
                  {d.revision_date ? ` · ред. від ${d.revision_date}` : ""}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
