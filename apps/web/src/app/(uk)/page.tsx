import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BarChart3, Clock, FileText, Search, ShieldAlert, User, Eye, Upload } from "lucide-react";
import { Loader } from "@/components/ui/loader";
import { Logo } from "@/components/ui/logo";

const metrics = [
  { label: "Документи в базі", value: "0", icon: FileText, note: "рахунок ведеться лише за реальними імпортованими актами" },
  { label: "Чинні документи", value: "0", icon: Eye, note: "статус підтверджений джерелом" },
  { label: "Нові надходження за період", value: "0", icon: Clock, note: "за останні 7 днів" },
  { label: "Зміни, що набрали чинності", value: "0", icon: FileText, note: "ревізії з дійсною датою вступу" },
  { label: "Майбутні зміни", value: "0", icon: Clock, note: "заплановані дати вступу в чинність" },
  { label: "Втратили чинність", value: "0", icon: ShieldAlert, note: "акти без чинної редакції" },
  { label: "Мої відстежувані норми", value: "0", icon: User, note: "активні правила моніторингу" },
  { label: "Завершені аналізи договорів", value: "0", icon: Upload, note: "структуровані звіти" },
];

const quickActions = [
  { label: "Знайти закон", href: "/uk/legislation", icon: Search },
  { label: "Порівняти редакції", href: "/uk/changes", icon: FileText },
  { label: "Проаналізувати договір", href: "/uk/contracts", icon: Upload },
  { label: "Поставити правове питання", href: "/uk/assistant", icon: BarChart3 },
  { label: "Створити моніторинг", href: "/uk/monitoring", icon: Eye },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <Loader />

      <div className="flex items-center gap-3 mb-4">
        <Logo className="w-8 h-8" />
        <span className="font-serif font-bold text-xl text-cream tracking-tight">AI Ugoda</span>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-text tracking-tight">Центр правової аналітики</h1>
        <p className="text-text-secondary">Актуальність законодавства, зміни та юридичні ризики в одному просторі.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm text-text-secondary">{m.label}</CardTitle>
              <m.icon className="h-5 w-5 text-crema" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-mono font-bold text-text">{m.value}</div>
              <p className="text-xs text-text-secondary/70 mt-2">{m.note}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <section className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Останні зміни законодавства</CardTitle>
          </CardHeader>
          <CardContent className="py-6">
            <div className="flex flex-col items-center justify-center py-10 text-text-secondary">
              <Clock className="mb-3 h-8 w-8 text-crema opacity-50" />
              <p className="text-sm">Змін ще не виявлено</p>
              <p className="text-xs text-text-secondary/60 mt-1">
                Після імпорту з data.rada.gov.ua тут з'являться підтверджені події зміни законодавства.
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Швидкі дії</CardTitle>
          </CardHeader>
          <CardContent className="py-2 space-y-2">
            {quickActions.map((a) => (
              <Button key={a.label} asChild variant="ghost" size="lg" className="w-full justify-start text-left border-b border-gold/10 last:border-0">
                <Link href={a.href}>
                  <a.icon className="mr-2 h-4 w-4 text-crema" />
                  {a.label}
                </Link>
              </Button>
            ))}
          </CardContent>
        </Card>
      </section>

      <div className="rounded-lg border border-gold/10 bg-elevated p-6 text-text-secondary">
        <p className="text-sm">
          <strong>Примітка про дані.</strong> Панель відображає лише значення, обчислені з реальних записів бази. Поки джерело data.rada.gov.ua не імпортовано, статистика дорівнює нулю — це цільово, щоб не вигадувати показники.
        </p>
      </div>
    </div>
  );
}