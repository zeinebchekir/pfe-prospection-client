import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building2, Users, Calendar, MapPin, Briefcase } from "lucide-react";
import type { MarketSegment } from "@/lib/segments-data";
import { RECOMMENDATION_STYLES, TOTAL_LEADS } from "@/lib/segments-data";

interface Props {
  segment: MarketSegment;
}

export function SegmentCard({ segment }: Props) {
  const share = Math.round((segment.count / TOTAL_LEADS) * 100);

  return (
    <Card className={`p-5 rounded-xl border-l-4 ${segment.tailwindBorder} hover:shadow-md transition-all`}>
      <div className="flex items-start justify-between mb-4">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-foreground text-sm leading-tight">{segment.name}</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold" style={{ color: segment.color }}>
              {segment.count}
            </span>
            <span className="text-xs text-muted-foreground">leads · {share}% du portefeuille</span>
          </div>
        </div>
        <Badge variant="outline" className="text-[10px] font-mono shrink-0">
          C{segment.clusterId}
        </Badge>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-muted/40 rounded-lg p-2">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wide">CA moyen</div>
          <div className="text-sm font-bold text-foreground mt-0.5">{segment.avgRevenueLabel}</div>
        </div>
        <div className="bg-muted/40 rounded-lg p-2">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Effectif</div>
          <div className="text-sm font-bold text-foreground mt-0.5">{segment.avgEmployees.toLocaleString("fr-FR")}</div>
        </div>
        <div className="bg-muted/40 rounded-lg p-2">
          <div className="text-[10px] text-muted-foreground uppercase tracking-wide">Âge moy.</div>
          <div className="text-sm font-bold text-foreground mt-0.5">{segment.avgAge} ans</div>
        </div>
      </div>

      <div className="space-y-1.5 mb-4">
        <Row icon={Building2} label="Catégorie" value={segment.dominantCategory} />
        <Row icon={Briefcase} label="Secteur" value={segment.dominantSector} />
        <Row icon={MapPin} label="Région" value={segment.dominantRegion} />
      </div>

      <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-medium border ${RECOMMENDATION_STYLES[segment.recommendation]}`}>
        {segment.recommendation}
      </div>
    </Card>
  );
}

function Row({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <Icon className="w-3 h-3 text-muted-foreground shrink-0" />
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground font-medium ml-auto truncate">{value}</span>
    </div>
  );
}
