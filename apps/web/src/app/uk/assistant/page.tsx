"use client";

import { useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { askAI } from "@/lib/api";
import { Scale } from "lucide-react";

type Answer = {
  answer: string;
  key_points: string[];
  citations: { provision_id: string; quote: string; verified: boolean }[];
  confidence: string;
  warnings: string[];
  provider: string;
};

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Answer | null>(null);

  const submit = async () => {
    if (!question.trim()) return;
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const res = await askAI(question.trim());
      setResult(res);
    } catch (e: any) {
      setError(e?.message || "Помилка запиту до AI");
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell
      title="AI Юрист-дослідник"
      subtitle="Пошуковий опис законодавства з посиланнями на отримані з джерела положення. AI не заміняє юриста."
    >
      <div className="space-y-4">
        <div className="glass card">
          <div className="flex gap-2">
            <input
              className="input flex-1"
              placeholder="Напр.: Який строк позовної давності за ЦК України?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
              }}
            />
            <button className="btn" onClick={submit} disabled={busy || !question.trim()}>
              {busy ? "Запит…" : "Запитати"}
            </button>
          </div>
          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
        </div>

        {result && (
          <div className="glass card">
            <div className="flex items-center gap-2 mb-2">
              <Scale className="h-4 w-4" />
              <h2 className="font-medium">Відповідь</h2>
              <span className="tag">
                провайдер: {result.provider}
                {result.provider !== "mock" && Number(result.confidence) > 0
                  ? ` · впевненість: ${Math.round(Number(result.confidence) * 100)}%`
                  : " · впевненість не обчислювалася"}
              </span>
            </div>
            <p style={{ whiteSpace: "pre-wrap" }}>{result.answer}</p>

            {result.key_points?.length > 0 && (
              <>
                <h3 className="font-medium mt-3">Ключові тези</h3>
                <ul className="list-disc ml-5">
                  {result.key_points.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </>
            )}

            {result.citations?.length > 0 && (
              <>
                <h3 className="font-medium mt-3">Цитування з джерела</h3>
                <div className="space-y-1">
                  {result.citations.map((c, i) => (
                    <div key={i} className="why">
                      <span className="tag">{c.verified ? "✓ підтверджено текстом норми" : "· не підтверджено"}</span>{" "}
                      {c.quote}
                    </div>
                  ))}
                </div>
              </>
            )}

            {result.warnings?.length > 0 && (
              <p className="tag mt-3">⚠ {result.warnings.join(" · ")}</p>
            )}
          </div>
        )}
      </div>
    </PageShell>
  );
}
