export default function Loading() {
  return (
    <div className="glass card" aria-busy="true">
      <div className="skeleton" style={{ height: 32, width: "40%", marginBottom: 16 }} />
      <div className="skeleton" style={{ height: 16, width: "100%", marginBottom: 10 }} />
      <div className="skeleton" style={{ height: 16, width: "92%", marginBottom: 10 }} />
      <div className="skeleton" style={{ height: 16, width: "84%" }} />
    </div>
  );
}
