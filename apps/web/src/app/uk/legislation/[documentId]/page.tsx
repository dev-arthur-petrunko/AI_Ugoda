"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { FileText } from "lucide-react";
import { getDocument, getProvisions, getRevisions } from "@/lib/api";

export default function LegislationDetailPage() {
  const params = useParams<{ documentId: string }>();
  const id = params?.documentId;
  const [doc, setDoc] = useState<any>(null);
  const [provs, setProvs] = useState<any[]>([]);
  const [revs, setRevs] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let alive = true;
    (async () => {
      try {
        const [d, p, r] = await Promise.all([getDocument(id), getProvisions(id), getRevisions(id)]);
        if (!alive) return;
        setDoc(d);
        setProvs(p.items || []);
        setRevs(r.items || []);
      } catch (e: any) {
        if (alive) setError(e?.message || "Документ не знайдено");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [id]);

  if (loading) return <PageShell title="Документ"><p className="text-sm text-text-secondary">Завантаження…</p></PageShell>;
  if (error || !doc) {
    return (
      <PageShell title="Акт не знайдено" subtitle={`Акт з ідентифікатором ${id} ще не імпортовано.`}>
        <EmptyState icon={<FileText className="h-5 w-5" />} title="Акт не знайдено" description={`Ідентифікатор: ${id}`} actionLabel="До пошуку" actionHref="/uk/legislation" />
      </PageShell>
    );
  }

  return (
    <PageShell title={doc.title} subtitle={doc.current_known_status}>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          <div className="text-sm text-text-secondary">{doc.issuing_authority} · {doc.adoption_date}</div>
          <div className="text-xs text-text-secondary/60">Джерело: {doc.source_url}</div>
          <div className="space-y-3">
            {provs.map((p) => (
              <div key={p.id} className="rounded-md border border-gold/10 bg-elevated p-3">
                <div className="font-mono text-xs text-gold">{p.identifier}</div>
                {p.heading && <div className="text-sm font-semibold mt-1">{p.heading}</div>}
                {p.text && <div className="text-sm text-text-secondary mt-1 whitespace-pre-wrap">{p.text}</div>}
              </div>
            ))}
            {provs.length === 0 && <p className="text-sm text-text-secondary">Структура ще не розібрана.</p>}
          </div>
        </div>
        <div className="space-y-4">
          <div className="rounded-md border border-gold/10 bg-elevated p-3">
            <div className="text-xs font-semibold text-text-secondary mb-2">Редакції</div>
            <ul className="space-y-1 text-xs">
              {revs.map((r) => (
                <li key={r.id} className="text-text-secondary">
                  {r.revision_date || "—"} · {r.verification_status}
                </li>
              ))}
              {revs.length === 0 && <li className="text-text-secondary/60">Немає</li>}
            </ul>
          </div>
        </div>
      </div>
    </PageShell>
  );
}