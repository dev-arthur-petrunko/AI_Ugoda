import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { ShieldAlert } from "lucide-react";

export default function ConflictsPage() {
  return (
    <PageShell
      title="Протиріччя та колізії"
      subtitle="Кандидати в неконсистентні положення з посиланнями на джерела. Знижка вимагає юридичної перевірки."
    >
      <EmptyState
        icon={<ShieldAlert className="h-5 w-5" />}
        title="Кандидатів у колізії не знайдено"
        description="Кандидати з\'являться після побудови графа посилань між положеннями актів."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}