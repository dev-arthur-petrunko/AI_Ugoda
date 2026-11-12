"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Clock } from "lucide-react";
import { listEvents, getSyncStatus, type ChangeEvent } from "@/lib/api";
import Link from "next/link";

export default function ChangesPage() {
  const [items, setItems] = useState<ChangeEvent[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [errMsg, setErrMsg] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [syncNote, setSyncNote] = useState<string | null>(null);

  const load = () => {
    setState("loading");
    Promise.all([
      listEvents(50, 0),
      getSyncStatus().catch(() => null),
    ])
      .then(([ev, sync]) => {
        setItems(ev.items || []);
        setTotal(ev.total || 0);
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
            description="Події зʼявляються з офіційних приміток джерела після імпорту редакцій з zakon.rada.gov.ua. Кожна подія містить статтю, акт-джерело та дату."
            actionLabel="Перейти на дашборд"
            actionHref="/uk"
          />
        )}

        {state === "ready" && items.length > 0 && (
          <div className="space-y-2">
            <p className="tag">
              Знайдено програмою: {total} подій змін (показано {items.length}) — з офіційних приміток
              джерела, не ШІ.
            </p>
            {items.map((e) => (
              <Link
                key={e.id}
                href={`/uk/legislation/${e.affected_document_id}`}
                className="glass card block hover:opacity-90"
              >
                <p className="font-medium">
                  <span className="tag">{e.event_label}</span>
                  {e.source_provision ? ` · ст. ${e.source_provision}` : ""}
                  {e.source_act_ref ? ` · ${e.source_act_ref}` : ""}
                </p>
                <p className="font-medium">{e.affected_title || e.affected_document_id}</p>
                <p className="tag">
                  {[
                    e.source_event_date ? `зміна від ${e.source_event_date}` : null,
                    e.source_title ? `джерело: ${e.source_title}` : null,
                  ]
                    .filter(Boolean)
                    .join(" · ") || "без дати в джерелі"}
                </p>
                {e.source_url && (
                  <p className="tag">
                    <a href={e.source_url} target="_blank" rel="noreferrer" className="underline">
                      офіційний текст
                    </a>
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
