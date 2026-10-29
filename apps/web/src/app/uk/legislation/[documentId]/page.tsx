"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { FileText } from "lucide-react";
import { getDocument, getProvisions, getRevisions, getAnalysis } from "@/lib/api";

export default function LegislationDetailPage() {
  const params = useParams<{ documentId: string }>();
  const id = params?.documentId;
  const [doc, setDoc] = useState<any>(null);
  const [provs, setProvs] = useState<any[]>([]);
  const [revs, setRevs] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"text" | "analysis">("text");

  useEffect(() => {
    if (!id) return;
    let alive = true;
    (async () => {
      try {
        const [d, p, r, a] = await Promise.all([getDocument(id), getProvisions(id), getRevisions(id), getAnalysis(id)]);
        if (!alive) return;
        setDoc(d);
        setProvs(p.items || []);
        setRevs(r.items || []);
        setAnalysis(a);
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
      <div className="flex gap-2 mb-4 border-b border-gold/10">
        <button
          onClick={() => setTab("text")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "text" ? "text-gold border-b-2 border-gold" : "text-text-secondary hover:text-text"}`}
        >
          Текст
        </button>
        <button
          onClick={() => setTab("analysis")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${tab === "analysis" ? "text-gold border-b-2 border-gold" : "text-text-secondary hover:text-text"}`}
        >
          Аналіз
        </button>
      </div>
      {tab === "text" && (
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
      )}
      {tab === "analysis" && analysis && (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <div className="glass card">
              <h2 className="text-lg font-semibold text-text mb-2">Базова аналітика акта</h2>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-md border border-gold/10 bg-elevated p-3">
                  <div className="text-xs text-text-secondary">Редакцій</div>
                  <div className="text-2xl font-bold text-gold">{analysis.metrics?.revisions_count ?? "—"}</div>
                </div>
                <div className="rounded-md border border-gold/10 bg-elevated p-3">
                  <div className="text-xs text-text-secondary">Положень</div>
                  <div className="text-2xl font-bold text-gold">{analysis.metrics?.provisions_count ?? "—"}</div>
                </div>
                <div className="rounded-md border border-gold/10 bg-elevated p-3">
                  <div className="text-xs text-text-secondary">Статей</div>
                  <div className="text-2xl font-bold text-gold">{analysis.metrics?.articles_count ?? "—"}</div>
                </div>
                <div className="rounded-md border border-gold/10 bg-elevated p-3">
                  <div className="text-xs text-text-secondary">Пунктів</div>
                  <div className="text-2xl font-bold text-gold">{analysis.metrics?.points_count ?? "—"}</div>
                </div>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="rounded-md border border-gold/10 bg-elevated p-3">
              <div className="text-xs font-semibold text-text-secondary mb-2">Редакції</div>
              <ul className="space-y-1 text-xs">
                {(analysis.revisions || []).map((r: any) => (
                  <li key={r.id} className="text-text-secondary">
                    {r.effective_from || "—"} · {r.verification_status}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </PageShell>
  );
}