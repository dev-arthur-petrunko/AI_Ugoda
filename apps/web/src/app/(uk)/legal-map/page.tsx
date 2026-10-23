import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Link as LinkIcon } from "lucide.react";

export default function LegalMapPage() {
  return (
    <PageShell
      title="Карта законодавства"
      subtitle="Взаємозв\'язки актів, статей та поправок з посиланням на джерело кожного ребра."
    >
      <EmptyState
        icon={<LinkIcon className="h-5 w-5" />}
        title="Граф ще не побудований"
        description="Вузли та ребра з\'являться після імпорту актів та вилучення посилань між положеннями."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}