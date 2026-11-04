"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { listDocuments, getGraph, type DocumentItem } from "@/lib/api";
import { Link as LinkIcon } from "lucide-react";

export default function LegalMapPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [docId, setDocId] = useState<string>("");
  const [state, setState] = useState<"loading" | "ready" | "error" | "empty">("empty");
  const [errMsg, setErrMsg] = useState<string | null>(null);
  const [graph, setGraph] = useState<{ nodes: any[]; edges: any[] } | null>(null);

  useEffect(() => {
    listDocuments("", 20, 0)
      .then((res) => {
        setDocs(res.items || []);
        setState("ready");
      })
      .catch((e: any) => {
        setErrMsg(e?.message || "Немає зв'язку з сервером");
        setState("error");
      });
  }, []);

  const loadGraph = (id: string) => {
    setDocId(id);
    setGraph(null);
    if (!id) return;
    setState("loading");
    getGraph(id)
      .then((g) => {
        setGraph({ nodes: g.nodes || [], edges: g.edges || [] });
        setState("ready");
      })
      .catch((e: any) => {
        setErrMsg(e?.message || "Немає зв'язку з сервером");
        setState("error");
      });
  };

  return (
    <PageShell
      title="Карта законодавства"
      subtitle="Взаємозв'язки актів, статей та поправок з посиланням на джерело кожного ребра."
    >
      <div className="space-y-4">
        <div className="glass card">
          <h2 className="font-medium mb-2">Оберіть акт</h2>
          <select className="input" value={docId} onChange={(e) => loadGraph(e.target.value)}>
            <option value="">— оберіть акт —</option>
            {docs.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </div>

        {state === "error" && (
          <div className="glass card text-center py-8">
            <p className="text-red-400 text-sm">{errMsg}</p>
            <button
              className="btn s"
              style={{ marginTop: 10 }}
              onClick={() => {
                if (docId) loadGraph(docId);
                else {
                  setState("loading");
                  listDocuments("", 20, 0)
                    .then((res) => {
                      setDocs(res.items || []);
                      setState("ready");
                    })
                    .catch((e: any) => setErrMsg(e?.message || "Немає зв'язку з сервером"));
                }
              }}
            >
              Повторити
            </button>
          </div>
        )}

        {state === "loading" && <p className="text-text-secondary">Завантаження графа…</p>}

        {state === "ready" && graph && (
          <div className="grid">
            <div className="glass card">
              <h2 className="font-medium mb-2">
                <LinkIcon className="h-4 w-4 inline mr-1" />
                Вузли ({graph.nodes.length})
              </h2>
              {graph.nodes.length === 0 ? (
                <p className="tag">Вузлів ще не вилучено для цього акта.</p>
              ) : (
                <div className="space-y-1">
                  {graph.nodes.map((n: any, i: number) => (
                    <div key={n.id || i} className="lvl">
                      <span>{n.label || n.title || n.id}</span>
                      <span className="tag">{n.type || ""}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="glass card">
              <h2 className="font-medium mb-2">Ребра ({graph.edges.length})</h2>
              {graph.edges.length === 0 ? (
                <p className="tag">Ребер ще не вилучено для цього акта.</p>
              ) : (
                <div className="space-y-1">
                  {graph.edges.map((e: any, i: number) => (
                    <div key={i} className="lvl">
                      <span>
                        {e.source} → {e.target}
                      </span>
                      <span className="tag">{e.type || e.relation_type || ""}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {state === "ready" && !graph && (
          <div className="glass card text-center py-8">
            <LinkIcon className="h-5 w-5 mx-auto mb-2 text-text-secondary" />
            <p className="text-sm text-text-secondary">
              Оберіть акт вище, щоб побачити вузли та ребра. Граф порожній, поки в базі немає
              вилучених посилань між положеннями.
            </p>
          </div>
        )}
      </div>
    </PageShell>
  );
}
