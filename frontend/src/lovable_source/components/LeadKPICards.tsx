import { Card } from "@/components/ui/card";
import { Building2, TrendingUp, Target, BarChart3, DollarSign, CheckCircle, Sparkles } from "lucide-react";
import { formatCA } from "@/lib/lead-adapter";

interface KPIs {
  total: number;
  avgScore: number;
  avgProba: number;
  avgCompletude: number;
  totalCA: number;
  qualified: number;
  opportunities: number;
}

const cards = [
  { key: "total" as const, label: "Total leads", icon: Building2, color: "text-tacir-blue", bg: "bg-blue-50" },
  { key: "avgScore" as const, label: "Score moyen", icon: TrendingUp, color: "text-emerald-600", bg: "bg-emerald-50", suffix: "/100" },
  { key: "avgProba" as const, label: "Proba. moy.", icon: Target, color: "text-amber-600", bg: "bg-amber-50", suffix: "%" },
  { key: "avgCompletude" as const, label: "Complétude moy.", icon: BarChart3, color: "text-blue-600", bg: "bg-blue-50", suffix: "%" },
  { key: "totalCA" as const, label: "CA cumulé", icon: DollarSign, color: "text-emerald-600", bg: "bg-emerald-50", isCA: true },
  { key: "qualified" as const, label: "Qualifiés", icon: CheckCircle, color: "text-tacir-blue", bg: "bg-blue-50" },
  { key: "opportunities" as const, label: "Opportunités", icon: Sparkles, color: "text-amber-600", bg: "bg-amber-50" },
];

export function LeadKPICards({ kpis }: { kpis: KPIs }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
      {cards.map((c) => {
        const Icon = c.icon;
        const val = kpis[c.key];
        const display = c.isCA ? formatCA(val) : `${val}${c.suffix ?? ""}`;
        return (
          <Card key={c.key} className="p-3 border-border shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-7 h-7 rounded-lg ${c.bg} flex items-center justify-center`}>
                <Icon className={`w-3.5 h-3.5 ${c.color}`} />
              </div>
            </div>
            <p className="text-lg font-semibold text-foreground leading-tight">{display}</p>
            <p className="text-[10px] text-muted-foreground">{c.label}</p>
          </Card>
        );
      })}
    </div>
  );
}
