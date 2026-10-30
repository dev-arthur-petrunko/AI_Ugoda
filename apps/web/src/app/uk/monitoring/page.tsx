"use client";

import { useState, useEffect } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { Eye, Plus, Trash2 } from "lucide-react";
import { listMonitoringRules, createMonitoringRule, deleteMonitoringRule } from "@/lib/api";

export default function MonitoringPage() {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [ruleType, setRuleType] = useState("");
  const [creating, setCreating] = useState(false);

  const loadRules = async () => {
    setLoading(true);
    try {
      const res = await listMonitoringRules();
      setRules(res.items || []);
      setError(null);
    } catch (e: any) {
      setError(e?.message || "Помилка завантаження");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadRules(); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ruleType.trim()) return;
    setCreating(true);
    try {
      await createMonitoringRule(ruleType.trim());
      setRuleType("");
      setShowForm(false);
      await loadRules();
    } catch (err: any) {
      setError(err?.message || "Помилка створення");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMonitoringRule(id);
      await loadRules();
    } catch (err: any) {
      setError(err?.message || "Помилка видалення");
    }
  };

  return (
    <PageShell
      title="Моніторинг законодавства"
      subtitle="Слідкуйте за актами, статтями, темами або ключовими словами та отримуйте сповіщення про зміни."
    >
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <button
            className="btn p flex items-center gap-2"
            onClick={() => setShowForm(!showForm)}
          >
            <Plus className="h-4 w-4" />
            Нове правило
          </button>
        </div>

        {showForm && (
          <form onSubmit={handleCreate} className="glass card space-y-3">
            <input
              className="field"
              placeholder="Тип правила (наприклад: document_change, keyword_match)"
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value)}
              required
            />
            <div className="flex gap-2">
              <button type="submit" className="btn p" disabled={creating}>
                {creating ? "Створення..." : "Створити"}
              </button>
              <button type="button" className="btn s" onClick={() => setShowForm(false)}>
                Скасувати
              </button>
            </div>
          </form>
        )}

        {error && <p className="text-red-400 text-sm">{error}</p>}

        {loading ? (
          <p className="text-text-secondary">Завантаження...</p>
        ) : rules.length === 0 ? (
          <div className="glass card text-center py-8">
            <Eye className="h-8 w-8 mx-auto mb-2 text-text-secondary" />
            <p className="text-text-secondary">Активних правил моніторингу немає</p>
            <p className="text-sm text-text-secondary mt-1">
              Створіть правило, щоб отримувати повідомлення про нові редакції та зміни чинності.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {rules.map((rule) => (
              <div key={rule.id} className="glass card flex justify-between items-center">
                <div>
                  <p className="font-medium">{rule.rule_type}</p>
                  <p className="text-sm text-text-secondary">
                    {rule.enabled ? "Увімкнено" : "Вимкнено"} · створено {new Date(rule.created_at).toLocaleDateString("uk-UA")}
                  </p>
                </div>
                <button
                  className="btn s flex items-center gap-1"
                  onClick={() => handleDelete(rule.id)}
                >
                  <Trash2 className="h-4 w-4" />
                  Видалити
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  );
}