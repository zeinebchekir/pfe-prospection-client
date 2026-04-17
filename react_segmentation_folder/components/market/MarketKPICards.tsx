import { Card } from "@/components/ui/card";
import { Users, Layers, Crown, DollarSign, Clock, Target } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface KPI {
  label: string;
  value: string;
  hint?: string;
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
}

interface Props {
  totalLeads: number;
  segmentsCount: number;
  dominantSegment: string;
  avgRevenue: string;
  avgAge: string;
  prioritySegment: string;
}

export function MarketKPICards({
  totalLeads,
  segmentsCount,
  dominantSegment,
  avgRevenue,
  avgAge,
  prioritySegment,
}: Props) {
  const kpis: KPI[] = [
    {
      label: "Total leads analysés",
      value: totalLeads.toLocaleString("fr-FR"),
      hint: "Portefeuille complet",
      icon: Users,
      iconBg: "bg-tacir-blue/10",
      iconColor: "text-tacir-blue",
    },
    {
      label: "Segments identifiés",
      value: String(segmentsCount),
      hint: "Issus du clustering",
      icon: Layers,
      iconBg: "bg-tacir-lightblue/10",
      iconColor: "text-tacir-lightblue",
    },
    {
      label: "Segment dominant",
      value: dominantSegment,
      hint: "Par volume",
      icon: Crown,
      iconBg: "bg-tacir-yellow/10",
      iconColor: "text-tacir-yellow",
    },
    {
      label: "CA moyen global",
      value: avgRevenue,
      hint: "Toutes catégories",
      icon: DollarSign,
      iconBg: "bg-tacir-green/10",
      iconColor: "text-tacir-green",
    },
    {
      label: "Âge moyen global",
      value: `${avgAge} ans`,
      hint: "Maturité moyenne",
      icon: Clock,
      iconBg: "bg-tacir-darkblue/10",
      iconColor: "text-tacir-darkblue",
    },
    {
      label: "Segment prioritaire",
      value: prioritySegment,
      hint: "Recommandation",
      icon: Target,
      iconBg: "bg-tacir-lightblue/10",
      iconColor: "text-tacir-lightblue",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
      {kpis.map((kpi) => {
        const Icon = kpi.icon;
        return (
          <Card key={kpi.label} className="p-4 rounded-xl border hover:shadow-md transition-all">
            <div className="flex items-start justify-between mb-3">
              <div className={`w-9 h-9 rounded-lg ${kpi.iconBg} flex items-center justify-center`}>
                <Icon className={`w-4 h-4 ${kpi.iconColor}`} />
              </div>
            </div>
            <div className="text-xs text-muted-foreground font-medium mb-1">{kpi.label}</div>
            <div className="text-lg font-bold text-foreground leading-tight truncate">{kpi.value}</div>
            {kpi.hint && <div className="text-[10px] text-muted-foreground mt-1">{kpi.hint}</div>}
          </Card>
        );
      })}
    </div>
  );
}
