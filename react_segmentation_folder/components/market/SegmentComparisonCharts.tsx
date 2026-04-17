import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { MarketSegment } from "@/lib/segments-data";

type Metric = "revenue" | "employees" | "age";

const METRIC_LABELS: Record<Metric, string> = {
  revenue: "CA moyen (M€)",
  employees: "Effectif moyen",
  age: "Âge moyen (ans)",
};

interface Props {
  segments: MarketSegment[];
}

export function SegmentComparisonCharts({ segments }: Props) {
  const [metric, setMetric] = useState<Metric>("revenue");

  const weightData = segments.map((s) => ({
    name: s.shortName,
    value: s.count,
    color: s.color,
  }));

  const compareData = segments.map((s) => ({
    name: s.shortName,
    revenue: Math.round(s.avgRevenue / 1_000_000),
    employees: s.avgEmployees,
    age: Math.round(s.avgAge),
    color: s.color,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Weights */}
      <Card className="p-5 rounded-xl">
        <div className="mb-4">
          <h3 className="font-semibold text-foreground text-sm">Poids des segments</h3>
          <p className="text-xs text-muted-foreground">Répartition des leads par segment</p>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weightData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" interval={0} />
              <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid hsl(var(--border))" }}
                formatter={(value: number) => [`${value} leads`, "Volume"]}
              />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {weightData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* Comparison */}
      <Card className="p-5 rounded-xl">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-foreground text-sm">Comparaison des segments</h3>
            <p className="text-xs text-muted-foreground">Métriques moyennes par segment</p>
          </div>
          <div className="flex items-center gap-1 bg-muted/40 rounded-lg p-1">
            {(Object.keys(METRIC_LABELS) as Metric[]).map((m) => (
              <Button
                key={m}
                variant={metric === m ? "default" : "ghost"}
                size="sm"
                className="h-7 text-[11px] px-2"
                onClick={() => setMetric(m)}
              >
                {m === "revenue" ? "CA" : m === "employees" ? "Effectif" : "Âge"}
              </Button>
            ))}
          </div>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={compareData} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" interval={0} />
              <YAxis tick={{ fontSize: 10 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid hsl(var(--border))" }}
                formatter={(value: number) => [value.toLocaleString("fr-FR"), METRIC_LABELS[metric]]}
              />
              <Bar dataKey={metric} radius={[6, 6, 0, 0]}>
                {compareData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  );
}
