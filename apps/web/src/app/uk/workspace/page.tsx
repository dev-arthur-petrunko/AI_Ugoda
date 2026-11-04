"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Folder } from "lucide-react";
import { listContracts } from "@/lib/api";

type Contract = {
  id: string;
  original_filename: string;
  processing_status: string | null;
  created_at: string;
};

export default function WorkspacePage() {
  const [items, setItems] = useState<Contract[]>([]);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const load = () => {
    setState("loading");
    listContracts()
      .then((res) => {
        setItems(res.items || []);
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
      title="Мої документи"
      subtitle="Приватне сховище завантажених документів. Доступно лише власнику."
    >
      <div className="space-y-4">
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
            icon={<Folder className="h-5 w-5" />}
            title="Документів ще немає"
            description="Завантажте договір або інший документ для приватного аналізу. Документи не потрапляють у спільний пошуковий індекс. Завантаження нових файлів відкриється після підключення сховища (наступні етапи)."
            actionLabel="Перейти на дашборд"
            actionHref="/uk"
          />
        )}

        {state === "ready" && items.length > 0 && (
          <div className="space-y-2">
            {items.map((c) => (
              <div key={c.id} className="glass card flex justify-between items-center">
                <div>
                  <p className="font-medium">{c.original_filename}</p>
                  <p className="tag">
                    {c.processing_status || "новий"} · {new Date(c.created_at).toLocaleDateString("uk-UA")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}
