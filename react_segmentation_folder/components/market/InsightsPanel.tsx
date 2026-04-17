import { Card } from "@/components/ui/card";
import { Lightbulb, TrendingUp, Users, Target, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Insight {
  icon: LucideIcon;
  iconColor: string;
  iconBg: string;
  title: string;
  text: string;
}

const INSIGHTS: Insight[] = [
  {
    icon: TrendingUp,
    iconColor: "text-tacir-blue",
    iconBg: "bg-tacir-blue/10",
    title: "Plus forte valeur moyenne",
    text: "Les grands groupes matures concentrent la plus forte valeur économique unitaire et justifient une approche enterprise dédiée.",
  },
  {
    icon: Target,
    iconColor: "text-tacir-lightblue",
    iconBg: "bg-tacir-lightblue/10",
    title: "Meilleur équilibre volume / valeur",
    text: "Les ETI établies diversifiées offrent le compromis optimal — volume significatif et valeur économique soutenue.",
  },
  {
    icon: Users,
    iconColor: "text-tacir-green",
    iconBg: "bg-tacir-green/10",
    title: "Approche self-serve",
    text: "Les petites structures jeunes sont mieux servies par une expérience self-serve scalable plutôt que par du sales direct.",
  },
  {
    icon: Sparkles,
    iconColor: "text-tacir-darkblue",
    iconBg: "bg-tacir-darkblue/10",
    title: "Niche à forte valeur",
    text: "Le segment commerce de gros est volumétriquement réduit mais sa valeur unitaire en fait une cible vente conseil rentable.",
  },
];

export function InsightsPanel() {
  return (
    <Card className="p-5 rounded-xl">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-tacir-yellow/10 flex items-center justify-center">
          <Lightbulb className="w-4 h-4 text-tacir-yellow" />
        </div>
        <div>
          <h3 className="font-semibold text-foreground text-sm">Insights clés</h3>
          <p className="text-xs text-muted-foreground">Recommandations exécutives</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {INSIGHTS.map((insight, i) => {
          const Icon = insight.icon;
          return (
            <div
              key={i}
              className="flex gap-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className={`w-8 h-8 rounded-lg ${insight.iconBg} flex items-center justify-center shrink-0`}>
                <Icon className={`w-4 h-4 ${insight.iconColor}`} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-foreground mb-1">{insight.title}</div>
                <p className="text-xs text-muted-foreground leading-relaxed">{insight.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
