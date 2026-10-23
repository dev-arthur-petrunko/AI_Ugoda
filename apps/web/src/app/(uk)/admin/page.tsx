import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { ShieldAlert } from "lucide-react";

export default function AdminPage() {
  return (
    <PageShell
      title="Панель адміністратора"
      subtitle="Синхронізація джерела, імпорт, міграції, стан індексу та аудит (лише для адміністраторів)."
    >
      <EmptyState
        icon={<ShieldAlert className="h-5 w-5" />}
        title="Доступ обмежено"
        description="Панель адміністратора доступна лише авторизованим адміністраторах на стороні сервера."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}