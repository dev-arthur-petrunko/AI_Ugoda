export default function ConflictsPage() {
  const LV = [
    "Конституція України",
    "Міжнародні договори (ратифіковані)",
    "Закони та кодекси",
    "Постанови Верховної Ради",
    "Укази Президента",
    "Постанови Кабінету Міністрів",
    "Накази міністерств",
    "Акти місцевих органів",
  ];
  const ladder = LV.map((n, i) => (
    <div key={i} className={`lvl ${i === 2 ? "hi" : i === 6 ? "lo" : ""}`}>
      <span>{n}</span>
      <span className="tag">{i === 2 ? "перемагає" : i === 6 ? "поступається" : ""}</span>
    </div>
  ));
  return (
    <>
      <h1 style={{ maxWidth: "18ch" }}>Протиріччя та колізії</h1>
      <p className="lead">Якщо дві норми суперечать, переможця визначають правила, а не здогадка.</p>
      <div className="grid">
        <div className="glass card">
          <h2>Рівні сили</h2>
          {ladder}
        </div>
        <div className="glass card">
          <h2>Правила вибору</h2>
          <div className="why">Вища сила перемагає нижчу.</div>
          <div className="why">Спеціальна норма перемагає загальну.</div>
          <div className="why">На одному рівні перемагає новіша.</div>
          <div className="why">Рішення Конституційного Суду скасовує норму.</div>
          <p className="sm" style={{ marginTop: 14 }}>Реальні колізії з'являться після імпорту та роботи детектора (етап 4).</p>
        </div>
      </div>
    </>
  );
}
