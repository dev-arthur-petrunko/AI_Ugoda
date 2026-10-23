import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Eye } from "lucide-react";

export default function MonitoringPage() {
  return (
    <PageShell
      title="Моніторинг законодавства"
      subtitle="Слідкуйте за актами, статтями, темами або ключовими словами та отримуйте сповіщення про зміни."
    >
      <EmptyState
        icon={<Eye className="h-5 w-5" />}
        title="Активних правил моніторингу немає"
        description="Створіть правило, щоб отримувати повідомлення про нові редакції та зміни чинності."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}