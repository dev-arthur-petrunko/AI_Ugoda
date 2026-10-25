import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Folder } from "lucide-react";

export default function WorkspacePage() {
  return (
    <PageShell
      title="Мої документи"
      subtitle="Приватне сховище завантажених документів. Доступно лише власнику."
    >
      <EmptyState
        icon={<Folder className="h-5 w-5" />}
        title="Документів ще немає"
        description="Завантажте договір або інший документ для приватного аналізу. Документи не потрапляють у спільний пошуковий індекс."
        actionLabel="Перейти на дашборд"
        actionHref="/uk"
      />
    </PageShell>
  );
}