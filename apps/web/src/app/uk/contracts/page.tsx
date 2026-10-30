"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { Upload, Trash2, FileText } from "lucide-react";
import { listContracts, getContract, deleteContract } from "@/lib/api";

export default function ContractsPage() {
  const [contracts, setContracts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<any | null>(null);

  const loadContracts = async () => {
    setLoading(true);
    try {
      const res = await listContracts();
      setContracts(res.items || []);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Помилка завантаження");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadContracts(); }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteContract(id);
      if (selected?.id === id) setSelected(null);
      await loadContracts();
    } catch (err: any) {
      setError(err?.message || "Помилка видалення");
    }
  };

  const handleSelect = async (id: string) => {
    try {
      const c = await getContract(id);
      setSelected(c);
    } catch (err: any) {
      setError(err?.message || "Помилка завантаження");
    }
  };

  return (
    <PageShell
      title="Аналіз договорів"
      subtitle="Завантажте договір (PDF, DOCX, TXT), щоб порівняти його положення з чинним законодавством."
    >
      <div className="space-y-4">
        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loading ? (
          <p className="text-text-secondary">Завантаження...</p>
        ) : contracts.length === 0 ? (
          <div className="glass card text-center py-8">
            <Upload className="h-8 w-8 mx-auto mb-2 text-text-secondary" />
            <p className="text-text-secondary">Немає завантажених договорів</p>
            <p className="text-sm text-text-secondary mt-1">
              Договори зберігаються приватно, лише для власника, та не потрапляють у спільний пошуковий індекс.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              {contracts.map((c) => (
                <div
                  key={c.id}
                  className={`glass card cursor-pointer ${selected?.id === c.id ? "border-gold" : ""}`}
                  onClick={() => handleSelect(c.id)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-text-secondary" />
                      <div>
                        <p className="font-medium">{c.original_filename}</p>
                        <p className="text-sm text-text-secondary">
                          {c.processing_status} · {(c.size_bytes / 1024).toFixed(1)} КБ
                        </p>
                      </div>
                    </div>
                    <button
                      className="btn s flex items-center gap-1"
                      onClick={(e) => { e.stopPropagation(); handleDelete(c.id); }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
            {selected && (
              <div className="glass card">
                <h2 className="font-semibold mb-2">{selected.original_filename}</h2>
                <p className="text-sm text-text-secondary">Тип: {selected.content_type}</p>
                <p className="text-sm text-text-secondary">Розмір: {(selected.size_bytes / 1024).toFixed(1)} КБ</p>
                <p className="text-sm text-text-secondary">Статус: {selected.processing_status}</p>
                <p className="text-sm text-text-secondary">Завантажено: {new Date(selected.created_at).toLocaleDateString("uk-UA")}</p>
                {selected.file_metadata && Object.keys(selected.file_metadata).length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-medium">Метадані:</p>
                    <pre className="text-xs bg-black/20 p-2 rounded mt-1 overflow-auto">
                      {JSON.stringify(selected.file_metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </PageShell>
  );
}