import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { FileText } from "lucide-react";

export default function ReportsPage() {
  return (
    <PageShell
      title="Звіти"
      subtitle="Експорт вивчальних мемо, звітів про зміни, аналізів договорів та порівнянь редакцій у PDF/DOCX."
    >
      <EmptyState
        icon={<FileText className="h-5 w-5" />}
        title="Немає звітів"
        description="Звіти генеруються на основі реальних записів і цитувань."
        actionLabel="Перейти на дашборд"
        actionHref="/uk/dashboard"
      />
    </PageShell>
  );
}