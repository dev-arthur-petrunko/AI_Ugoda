"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { Button } from "@/components/ui/button";
import { getSyncStatus, getSyncRuns, runSync } from "@/lib/api";

type RunReport = {
  duration_sec?: number;
  failed?: { url: string; reason: string }[];
  warnings?: { message: string; source_url?: string }[];
  parse_errors?: number;
  discovered?: number;
  added?: number;
  updated?: number;
  skipped?: number;
  errors?: number;
};

type Run = {
  id: string;
  source: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  added: number;
  updated: number;
  skipped: number;
  errors: number;
  report?: RunReport | null;
};

function St({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-gold/10 bg-elevated p-3">
      <div className="text-xs text-text-secondary">{label}</div>
      <div className="text-2xl font-bold text-gold">{value}</div>
    </div>
  );
}

export default function AdminPage() {
  const [status, setStatus] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<Run[]>([]);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const loadRuns = async () => {
    try {
      const r = await getSyncRuns(5);
      setRuns(r.items || []);
    } catch {
      /* історія не критична */
    }
  };

  useEffect(() => {
    getSyncStatus().then(setStatus).catch((e) => setError(e?.message));
    loadRuns();
  }, []);

  async function onRun() {
    setRunning(true);
    setError(null);
    try {
      const r = await runSync();
      setResult(r);
      // Імпорт іде у фоні (POST повертає лише старт) — опитуємо звіт /sync/runs.
      await new Promise((res) => setTimeout(res, 2500));
      await loadRuns();
    } catch (e: any) {
      setError(e?.message || "Помилка");
    } finally {
      setRunning(false);
    }
  }

  const last = runs[0];
  const report: RunReport | undefined = last?.report ?? undefined;
  const connectors = Array.isArray(status?.connectors) ? status.connectors : [];

  return (
    <PageShell title="Панель адміністратора" subtitle="Керування імпортом, стан джерел.">
      <div className="space-y-4">
        {/* Стан джерел (білий список) */}
        <div className="rounded-md border border-gold/10 bg-elevated p-3 text-sm">
          <div className="text-xs font-semibold text-text-secondary mb-2">Стан джерел</div>
          <div className="flex flex-wrap gap-2">
            {connectors.length > 0 ? (
              connectors.map((c: string) => (
                <span key={c} className="tag">{c}</span>
              ))
            ) : (
              <span className="tag">завантаження…</span>
            )}
            <span className="tag">
              блокування імпорту: {status?.import_locked ? "так" : "ні"}
            </span>
          </div>
        </div>

        <Button variant="gold" onClick={onRun} disabled={running}>
          {running ? "Запускається:" : "Запустити синхронізацію"}
        </Button>
        {error && <p className="text-sm text-red-400">{error}</p>}

        {/* Звіт імпорту: час, що не імпортовано/чому, попередження */}
        {last && (
          <div className="glass card">
            <h2 className="text-lg font-semibold text-text mb-2">Звіт імпорту</h2>
            <p className="text-xs text-text-secondary">
              {last.source} · статус: <b>{last.status}</b>
              {last.started_at ? ` · старт ${new Date(last.started_at).toLocaleString("uk-UA")}` : ""}
            </p>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-5 mt-3">
              <St label="Тривалість" value={report?.duration_sec != null ? `${report.duration_sec} с` : "—"} />
              <St label="Знайдено" value={report?.discovered ?? "—"} />
              <St label="Додано" value={last.added} />
              <St label="Оновлено" value={last.updated} />
              <St label="Помилок" value={last.errors} />
            </div>

            <div className="text-xs font-semibold text-text-secondary mt-4 mb-1">
              Не імпортовано ({report?.failed?.length ?? 0})
            </div>
            {report?.failed?.length ? (
              <ul className="space-y-1 text-xs text-text-secondary">
                {report.failed.map((f) => (
                  <li key={f.url}>
                    <span className="font-mono">{f.url}</span> — {f.reason}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-text-secondary/60">Усі акти з переліку успішно оброблено.</p>
            )}

            {report?.warnings?.length ? (
              <>
                <div className="text-xs font-semibold text-text-secondary mt-3 mb-1">
                  Попередження ({report.warnings.length})
                </div>
                <ul className="space-y-1 text-xs text-[#E0A23B]">
                  {report.warnings.map((w, i) => (
                    <li key={i}>{w.message}{w.source_url ? ` (${w.source_url})` : ""}</li>
                  ))}
                </ul>
              </>
            ) : null}
            {typeof report?.parse_errors === "number" && report.parse_errors > 0 && (
              <p className="text-xs text-red-400 mt-3">Помилок розбору: {report.parse_errors}</p>
            )}
          </div>
        )}

        {/* Попередні запуски */}
        {runs.length > 1 && (
          <div className="rounded-md border border-gold/10 bg-elevated p-3 text-xs text-text-secondary">
            <div className="font-semibold mb-1">Попередні запуски</div>
            <ul className="space-y-1">
              {runs.slice(1).map((r) => (
                <li key={r.id}>
                  {r.started_at ? new Date(r.started_at).toLocaleString("uk-UA") : r.id.slice(0, 8)} — {r.status} ·
                  +{r.added}/~{r.updated} · помилок: {r.errors}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Сирий відповідь ендпоінта запуску — для діагностики */}
        {result && (
          <div className="rounded-md border border-gold/10 bg-elevated p-3 text-xs text-text-secondary">
            <div className="font-semibold mb-1">POST /sync/run</div>
            <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </div>
    </PageShell>
  );
}
