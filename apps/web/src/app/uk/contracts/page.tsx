import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Upload } from "lucide-react";

export default function ContractsPage() {
  return (
    <PageShell
      title="Аналіз договорів"
      subtitle="Завантажте договір (PDF, DOCX, TXT), щоб порівняти його положення з чинним законодавством."
    >
      <EmptyState
        icon={<Upload className="h-5 w-5" />}
        title="Немає завантажених договорів"
        description="Договори зберігаються приватно, лише для власника, та не потрапляють у спільний пошуковий індекс."
        actionLabel="Перейти на дашборд"
        actionHref="/uk"
      />
    </PageShell>
  );
}