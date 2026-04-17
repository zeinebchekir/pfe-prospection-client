import { useMemo } from "react";
import type { MarketSegment } from "@/lib/segments-data";

interface Props {
  segments: MarketSegment[];
  total: number;
}

interface PositionedBubble extends MarketSegment {
  cx: number;
  cy: number;
  r: number;
  percent: number;
}

// Simple deterministic positioning based on segment count (largest center, others around)
const POSITIONS: { x: number; y: number }[] = [
  { x: 50, y: 50 },
  { x: 22, y: 38 },
  { x: 78, y: 40 },
  { x: 32, y: 75 },
  { x: 72, y: 75 },
];

export function SegmentBubbleChart({ segments, total }: Props) {
  const bubbles = useMemo<PositionedBubble[]>(() => {
    const sorted = [...segments].sort((a, b) => b.count - a.count);
    const maxCount = sorted[0]?.count ?? 1;

    return sorted.map((s, i) => {
      const ratio = s.count / maxCount;
      // radius scales between 6% and 18% of viewBox width
      const r = 6 + ratio * 12;
      const pos = POSITIONS[i] ?? { x: 50, y: 50 };
      return {
        ...s,
        cx: pos.x,
        cy: pos.y,
        r,
        percent: Math.round((s.count / total) * 100),
      };
    });
  }, [segments, total]);

  return (
    <div className="relative w-full" style={{ aspectRatio: "16 / 9" }}>
      <svg viewBox="0 0 100 56" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
        {bubbles.map((b) => (
          <g key={b.id} className="cursor-pointer transition-transform hover:scale-105" style={{ transformOrigin: `${b.cx}% ${b.cy}%` }}>
            <circle
              cx={b.cx}
              cy={b.cy * 0.56}
              r={b.r}
              fill={b.color}
              fillOpacity={0.18}
              stroke={b.color}
              strokeWidth={0.3}
            />
            <circle cx={b.cx} cy={b.cy * 0.56} r={b.r * 0.5} fill={b.color} fillOpacity={0.35} />
          </g>
        ))}
      </svg>
      {/* HTML overlay for crisp text */}
      <div className="absolute inset-0 pointer-events-none">
        {bubbles.map((b) => (
          <div
            key={b.id}
            className="absolute -translate-x-1/2 -translate-y-1/2 text-center pointer-events-auto"
            style={{
              left: `${b.cx}%`,
              top: `${(b.cy * 0.56 / 56) * 100}%`,
              maxWidth: `${b.r * 2.2}%`,
            }}
          >
            <div className="text-[11px] font-semibold leading-tight" style={{ color: b.color }}>
              {b.shortName}
            </div>
            <div className="text-[10px] font-bold text-foreground mt-0.5">{b.percent}%</div>
            <div className="text-[9px] text-muted-foreground">{b.count} leads</div>
          </div>
        ))}
      </div>
    </div>
  );
}
