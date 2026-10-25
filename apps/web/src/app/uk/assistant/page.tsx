import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { BarChart3 } from "lucide-react";

export default function AssistantPage() {
  return (
    <PageShell
      title="AI Юрист-дослідник"
      subtitle="Пошуковий опис законодавства з посиланнями на отримані з джерела положення. AI не заміняє юриста."
    >
      <EmptyState
        icon={<BarChart3 className="h-5 w-5" />}
        title="Немає досліджень"
        description="Задайте правове питання, щоб отримати відповідь із цитуваннями статей zakon.rada.gov.ua."
        actionLabel="Перейти на дашборд"
        actionHref="/uk"
      />
    </PageShell>
  );
}