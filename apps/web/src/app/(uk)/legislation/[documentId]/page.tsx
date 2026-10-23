import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { FileText, Link as LinkIcon } from "lucide.react";

export default function LegislationDetailPage({
  params,
}: {
  params: { documentId: string };
}) {
  return (
    <PageShell
      title="Документ"
      subtitle="Повний текст акта, метадані, історія ревізій та посилання на офіційне джерело."
    >
      <EmptyState
        icon={<FileText className="h-5 w-5" />}
        title="Документ не знайдено"
        description={`Акт з ідентифікатором ${params.documentId} ще не імпортовано з zakon.rada.gov.ua.`}
        actionLabel="Перейти до пошуку"
        actionHref="/uk/legislation"
      />
      <div className="mt-6">
        <a href="#" className="text-xs text-gold underline">
          Відкрити на zakon.rada.gov.ua
        </a>
        <span className="ml-2 text-xs text-text-secondary/60">· джерело акта</span>
      </div>
    </PageShell>
  );
}