import Link from "next/link";

export default function NotFound() {
  return (
    <div className="glass card">
      <h1>Сторінку не знайдено</h1>
      <p className="lead">Такого розділу не існує.</p>
      <Link className="btn p" href="/uk">
        На головну
      </Link>
    </div>
  );
}
