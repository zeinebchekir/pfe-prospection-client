import { Card } from "@/components/ui/card";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ZAxis,
  ReferenceLine,
} from "recharts";
import type { MarketSegment } from "@/lib/segments-data";

interface Props {
  segments: MarketSegment[];
}

export function OpportunityMatrix({ segments }: Props) {
  const data = segments.map((s) => ({
    name: s.shortName,
    x: s.count,
    y: s.avgRevenue / 1_000_000, // M€
    z: s.count,
    color: s.color,
  }));

  const maxX = Math.max(...data.map((d) => d.x));
  const maxY = Math.max(...data.map((d) => d.y));
  const midX = maxX / 2;
  const midY = maxY / 2;

  return (
    <Card className="p-5 rounded-xl">
      <div className="mb-4">
        <h3 className="font-semibold text-foreground text-sm">Priorisation commerciale</h3>
        <p className="text-xs text-muted-foreground">
          Matrice volume × valeur — chaque bulle = un segment
        </p>
      </div>

      <div className="relative h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 20, right: 30, bottom: 40, left: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              dataKey="x"
              name="Volume"
              tick={{ fontSize: 10 }}
              stroke="hsl(var(--muted-foreground))"
              label={{ value: "Volume de leads →", position: "insideBottom", offset: -10, fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Valeur (M€)"
              tick={{ fontSize: 10 }}
              stroke="hsl(var(--muted-foreground))"
              label={{ value: "Valeur estimée (M€) →", angle: -90, position: "insideLeft", fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
            />
            <ZAxis type="number" dataKey="z" range={[200, 1500]} />
            <ReferenceLine x={midX} stroke="hsl(var(--border))" strokeDasharray="4 4" />
            <ReferenceLine y={midY} stroke="hsl(var(--border))" strokeDasharray="4 4" />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{ borderRadius: 8, fontSize: 12, border: "1px solid hsl(var(--border))" }}
              formatter={(value: number, name: string) => {
                if (name === "Volume") return [`${value} leads`, "Volume"];
                if (name === "Valeur (M€)") return [`${value.toFixed(0)} M€`, "Valeur moy."];
                return [value, name];
              }}
              labelFormatter={() => ""}
            />
            <Scatter data={data}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.color} fillOpacity={0.7} stroke={d.color} strokeWidth={1.5} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Quadrant labels */}
        <div className="pointer-events-none absolute inset-0">
          <span className="absolute top-2 right-4 text-[10px] font-semibold text-tacir-blue uppercase tracking-wider opacity-70">
            Investir maintenant
          </span>
          <span className="absolute top-2 left-12 text-[10px] font-semibold text-tacir-yellow uppercase tracking-wider opacity-70">
            Opportunité long terme
          </span>
          <span className="absolute bottom-10 right-4 text-[10px] font-semibold text-tacir-green uppercase tracking-wider opacity-70">
            Nurture / automatiser
          </span>
          <span className="absolute bottom-10 left-12 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider opacity-70">
            Segment niche
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-4 pt-4 border-t">
        {segments.map((s) => (
          <div key={s.id} className="flex items-center gap-1.5 text-[11px]">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
            <span className="text-muted-foreground">{s.shortName}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}
