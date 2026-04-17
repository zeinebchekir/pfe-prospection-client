import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from "recharts";
import type { MarketSegment } from "@/lib/segments-data";

interface Props {
  segments: MarketSegment[];
}

const AXES = [
  "Taille entreprise",
  "Valeur économique",
  "Ancienneté",
  "Empreinte multi-sites",
  "Concentration géo.",
] as const;

// Normalize segment values to 0-100 for radar
function buildRadarData(selected: MarketSegment[]) {
  const maxEmp = Math.max(...selected.map((s) => s.avgEmployees), 1);
  const maxRev = Math.max(...selected.map((s) => s.avgRevenue), 1);
  const maxAge = Math.max(...selected.map((s) => s.avgAge), 1);
  const maxLoc = Math.max(...selected.map((s) => s.avgLocations), 1);

  return AXES.map((axis) => {
    const row: Record<string, string | number> = { axis };
    selected.forEach((s) => {
      let v = 0;
      switch (axis) {
        case "Taille entreprise":
          v = (s.avgEmployees / maxEmp) * 100;
          break;
        case "Valeur économique":
          v = (s.avgRevenue / maxRev) * 100;
          break;
        case "Ancienneté":
          v = (s.avgAge / maxAge) * 100;
          break;
        case "Empreinte multi-sites":
          v = (s.avgLocations / maxLoc) * 100;
          break;
        case "Concentration géo.":
          // Île-de-France dominance proxy
          v = s.dominantRegion === "Île-de-France" ? 90 : 50;
          break;
      }
      row[s.shortName] = Math.round(v);
    });
    return row;
  });
}

export function SegmentRadarChart({ segments }: Props) {
  const [selected, setSelected] = useState<string[]>(() =>
    segments.slice(0, 3).map((s) => s.id),
  );

  const toggle = (id: string) => {
    setSelected((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 3) return [...prev.slice(1), id];
      return [...prev, id];
    });
  };

  const activeSegments = segments.filter((s) => selected.includes(s.id));
  const data = buildRadarData(activeSegments);

  return (
    <Card className="p-5 rounded-xl">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <h3 className="font-semibold text-foreground text-sm">Comparaison multidimensionnelle</h3>
          <p className="text-xs text-muted-foreground">Sélectionnez jusqu'à 3 segments</p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {segments.map((s) => {
            const active = selected.includes(s.id);
            return (
              <button
                key={s.id}
                onClick={() => toggle(s.id)}
                className={`text-[11px] px-2.5 py-1 rounded-full border transition-all ${
                  active
                    ? "border-transparent text-white shadow-sm"
                    : "bg-background text-muted-foreground border-border hover:border-muted-foreground/40"
                }`}
                style={active ? { backgroundColor: s.color } : undefined}
              >
                {s.shortName}
              </button>
            );
          })}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data} outerRadius="75%">
            <PolarGrid stroke="hsl(var(--border))" />
            <PolarAngleAxis dataKey="axis" tick={{ fontSize: 11, fill: "hsl(var(--foreground))" }} />
            <PolarRadiusAxis tick={{ fontSize: 9 }} stroke="hsl(var(--muted-foreground))" angle={90} />
            <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid hsl(var(--border))" }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {activeSegments.map((s) => (
              <Radar
                key={s.id}
                name={s.shortName}
                dataKey={s.shortName}
                stroke={s.color}
                fill={s.color}
                fillOpacity={0.2}
              />
            ))}
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
