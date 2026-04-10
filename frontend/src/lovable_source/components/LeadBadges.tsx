import { Badge } from "@/components/ui/badge";
import type { LeadSegment, LeadStatus } from "@/types/lead";

const SEGMENT_STYLES: Record<LeadSegment, string> = {
  PME: "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100",
  ETI: "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100",
  GE: "bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100",
  Micro: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100",
  Inconnu: "bg-muted text-muted-foreground border-border",
};

const STATUS_STYLES: Record<LeadStatus, string> = {
  Nouveau: "bg-blue-50 text-blue-700 border-blue-200",
  Qualifié: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Opportunité: "bg-amber-50 text-amber-700 border-amber-200",
};

export function SegmentBadge({ segment }: { segment: LeadSegment }) {
  return (
    <Badge variant="outline" className={`text-[10px] font-semibold px-2 py-0.5 ${SEGMENT_STYLES[segment]}`}>
      {segment}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: LeadStatus }) {
  return (
    <Badge variant="outline" className={`text-[10px] font-semibold px-2 py-0.5 ${STATUS_STYLES[status]}`}>
      {status}
    </Badge>
  );
}

export function BoampBadge() {
  return (
    <Badge variant="outline" className="text-[10px] font-semibold px-2 py-0.5 bg-blue-50 text-tacir-blue border-blue-200">
      BOAMP
    </Badge>
  );
}

export function ScoreRing({ score, size = "sm" }: { score: number; size?: "sm" | "md" }) {
  const color =
    score >= 70 ? "text-emerald-700 bg-emerald-50" :
    score >= 40 ? "text-blue-700 bg-blue-50" :
    "text-orange-700 bg-orange-50";
  const dim = size === "md" ? "w-10 h-10 text-sm" : "w-7 h-7 text-[11px]";
  return (
    <span className={`inline-flex items-center justify-center rounded-full font-semibold ${color} ${dim}`}>
      {score}
    </span>
  );
}

export function CompletionBar({ value, showLabel = true }: { value: number; showLabel?: boolean }) {
  const color =
    value >= 70 ? "bg-emerald-500" :
    value >= 40 ? "bg-blue-500" :
    "bg-orange-500";
  return (
    <div className="flex items-center gap-2">
      <div className="w-12 h-1.5 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      {showLabel && <span className="text-[11px] font-medium text-muted-foreground">{value}%</span>}
    </div>
  );
}
