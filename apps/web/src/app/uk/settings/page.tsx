"use client";

import { useEffect, useState } from "react";
import { PageShell } from "@/components/layout/page-shell";
import { login as apiLogin, register as apiRegister, logout as apiLogout, getToken } from "@/lib/api";
import { LogIn, LogOut, UserPlus } from "lucide-react";

export default function SettingsPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    setAuthed(Boolean(getToken()));
  }, []);

  const run = async (fn: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setError(null);
    setOk(null);
    try {
      await fn();
      setOk(success);
      setAuthed(Boolean(getToken()));
    } catch (e: any) {
      setError(e?.message || "Помилка");
    } finally {
      setBusy(false);
    }
  };

  return (
    <PageShell
      title="Налаштування"
      subtitle="Обліковий запис, мова інтерфейсу, канали сповіщень та правила зберігання документів."
    >
      <div className="space-y-4">
        <div className="glass card">
          <h2 className="font-medium mb-1">Обліковий запис</h2>
          <p className="text-sm text-text-secondary mb-3">
            Вхід потрібен для закладок, моніторингу та договорів (захищені ендпоінти вимагають JWT).
          </p>

          {authed ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-text-secondary">Ви увійшли як {email || "користувач"}.</span>
              <button
                className="btn s flex items-center gap-1"
                onClick={() => {
                  apiLogout();
                  setAuthed(false);
                  setOk("Вихід виконано.");
                }}
              >
                <LogOut className="h-4 w-4" />
                Вийти
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2 max-w-md">
              <input
                type="email"
                className="input"
                placeholder="Електронна пошта"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <input
                type="password"
                className="input"
                placeholder="Пароль"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  className="btn flex items-center gap-1"
                  disabled={busy || !email || !password}
                  onClick={() => run(() => apiLogin(email, password), "Вхід виконано.")}
                >
                  <LogIn className="h-4 w-4" />
                  Увійти
                </button>
                <button
                  className="btn s flex items-center gap-1"
                  disabled={busy || !email || !password}
                  onClick={() =>
                    run(async () => {
                      await apiRegister(email, password);
                      await apiLogin(email, password);
                    }, "Реєстрацію завершено.")
                  }
                >
                  <UserPlus className="h-4 w-4" />
                  Зареєструватися
                </button>
              </div>
            </div>
          )}

          {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
          {ok && <p className="text-sm mt-2" style={{ color: "var(--gold, #c9a961)" }}>{ok}</p>}
        </div>

        <div className="glass card">
          <h2 className="font-medium mb-1">Мова та сповіщення</h2>
          <p className="text-sm text-text-secondary">
            Мова інтерфейсу: українська. Канали сповіщень (email/Telegram) зʼявляться після підключення
            черги розсилок — це наступні етапи плану.
          </p>
        </div>
      </div>
    </PageShell>
  );
}
