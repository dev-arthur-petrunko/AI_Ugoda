"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { Button } from "@/components/ui/button";
import { getSyncStatus, runSync } from "@/lib/api";

export default function AdminPage() {
  const [status, setStatus] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSyncStatus().then(setStatus).catch((e) => setError(e?.message));
  }, []);

  async function onRun() {
    setRunning(true);
    setError(null);
    try {
      const r = await runSync();
      setResult(r);
    } catch (e: any) {
      setError(e?.message || "Помилка");
    } finally {
      setRunning(false);
    }
  }

  return (
    <PageShell title="Панель адміністратора" subtitle="Синхронізація джерела, стан конекторів.">
      <div className="space-y-4">
        <div className="rounded-md border border-gold/10 bg-elevated p-3 text-sm">
          <pre className="whitespace-pre-wrap text-xs text-text-secondary">{JSON.stringify(status, null, 2)}</pre>
        </div>
        <Button variant="gold" onClick={onRun} disabled={running}>{running ? "Синхронізація…" : "Запустити синхронізацію"}</Button>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {result && <div className="rounded-md border border-gold/10 bg-elevated p-3 text-xs text-text-secondary"><pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre></div>}
      </div>
    </PageShell>
  );
}