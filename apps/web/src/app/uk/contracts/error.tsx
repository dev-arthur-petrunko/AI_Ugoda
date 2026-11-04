"use client";

export default function ErrorState({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <div className="glass card" role="alert">
      <h1>Помилка завантаження</h1>
      <p className="lead">{error.message || "Щось пішло не так. Спробуйте ще раз."}</p>
      <button className="btn p" onClick={reset}>
        Повторити
      </button>
    </div>
  );
}
