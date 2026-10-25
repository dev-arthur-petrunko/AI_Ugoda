import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Clock } from "lucide-react";

export default function ChangesPage() {
  return (
    <PageShell
      title="Нові закони та зміни"
      subtitle="Події законодавства: нові акти, поправки, дати вступу в чинність та втрата чинності."
    >
      <EmptyState
        icon={<Clock className="h-5 w-5" />}
        title="Лента змін ще порожня"
        description="Виявлені зміни зʼявляться після імпорту ревізій з zakon.rada.gov.ua. Кожна подія містить посилання на джерело та дату відкриття."
        actionLabel="Перейти на дашборд"
        actionHref="/uk"
      />
    </PageShell>
  );
}