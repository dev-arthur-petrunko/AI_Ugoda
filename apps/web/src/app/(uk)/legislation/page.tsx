import { PageShell } from "@/components/layout/page-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import Link from "next/link";

export default function LegislationPage() {
  return (
    <PageShell
      title="Пошук законодавства"
      subtitle="Каталог актів офіційного порталу zakon.rada.gov.ua з пошуком за назвою, текстом і реквізитами."
    >
      <div className="flex flex-col lg:flex-row gap-4">
        <div className="flex-1 max-w-2xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-secondary/60" />
            <Input placeholder="Введіть назву, номер або текст документу…" className="pl-10" />
          </div>
          <div className="mt-4 flex flex-wrap gap-2 text-xs text-text-secondary/60">
            <span>Режими:</span>
            <span className="bg-elevated px-2 py-1 rounded border border-gold/10">в назві</span>
            <span className="bg-elevated px-2 py-1 rounded border border-gold/10">у тексті</span>
            <span className="bg-elevated px-2 py-1 rounded border border-gold/10">за номером</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="gold">Шукати</Button>
          <Button variant="gold-outline">Фільтри</Button>
        </div>
      </div>

      <div className="mt-6">
        <Card>
          <CardHeader>
            <CardTitle>Результати пошуку</CardTitle>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={<Search className="h-5 w-5" />}
              title="Каталог ще порожній"
              description="Документи зʼявяться після імпорту з zakon.rada.gov.ua. Пошук працюватиме над реальними записами бази."
              actionLabel="Перейти на дашборд"
              actionHref="/uk/dashboard"
            />
          </CardContent>
        </Card>
      </div>
    </PageShell>
  );
}