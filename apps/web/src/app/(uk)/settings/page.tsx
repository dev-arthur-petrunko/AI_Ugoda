import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <PageShell
      title="Налаштування"
      subtitle="Обліковий запис, мова інтерфейсу, канали сповіщень та правила зберігання документів."
    >
      <EmptyState
        icon={<Settings className="h-5 w-5" />}
        title="Налаштування"
        description="Сторінка налаштувань буде додана на наступному етапі."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}