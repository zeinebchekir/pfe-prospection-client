import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { SegmentBadge, StatusBadge, BoampBadge, ScoreRing, CompletionBar } from "./LeadBadges";
import { ChevronDown, ChevronUp, Eye, Pencil, Trash2 } from "lucide-react";
import type { UILead } from "@/types/lead";
import type { SortField, SortDir } from "@/hooks/use-leads";
import { Skeleton } from "@/components/ui/skeleton";

interface Props {
  leads: UILead[];
  sortField: SortField;
  sortDir: SortDir;
  onSort: (field: SortField) => void;
  onPreview: (lead: UILead) => void;
  onEdit: (lead: UILead) => void;
  onDelete: (lead: UILead) => void;
  onNavigate: (lead: UILead) => void;
  loading?: boolean;
}

function SortIcon({ field, current, dir }: { field: SortField; current: SortField; dir: SortDir }) {
  if (field !== current) return <ChevronDown className="w-3 h-3 opacity-30" />;
  return dir === "asc" ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />;
}

function SortableHead({ field, label, current, dir, onSort }: {
  field: SortField; label: string; current: SortField; dir: SortDir; onSort: (f: SortField) => void;
}) {
  return (
    <TableHead
      className="cursor-pointer select-none hover:bg-muted/50 transition-colors text-[11px] font-medium whitespace-nowrap"
      onClick={() => onSort(field)}
    >
      <span className="flex items-center gap-1">
        {label}
        <SortIcon field={field} current={current} dir={dir} />
      </span>
    </TableHead>
  );
}

export function LeadTable({ leads, sortField, sortDir, onSort, onPreview, onEdit, onDelete, onNavigate, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-2 p-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-10 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (leads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-4">
          <Eye className="w-7 h-7 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium text-foreground mb-1">Aucun lead trouvé</p>
        <p className="text-xs text-muted-foreground">Ajustez vos filtres ou ajoutez un nouveau lead</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <SortableHead field="nom" label="Entreprise" current={sortField} dir={sortDir} onSort={onSort} />
            <SortableHead field="segment" label="Segment" current={sortField} dir={sortDir} onSort={onSort} />
            <TableHead className="text-[11px] font-medium whitespace-nowrap">Secteur</TableHead>
            <SortableHead field="ville" label="Ville" current={sortField} dir={sortDir} onSort={onSort} />
            <TableHead className="text-[11px] font-medium whitespace-nowrap">SIREN</TableHead>
            <SortableHead field="ca" label="CA" current={sortField} dir={sortDir} onSort={onSort} />
            <SortableHead field="nbLocaux" label="Locaux" current={sortField} dir={sortDir} onSort={onSort} />
            <SortableHead field="score" label="Score" current={sortField} dir={sortDir} onSort={onSort} />
            <SortableHead field="completude" label="Complétude" current={sortField} dir={sortDir} onSort={onSort} />
            <TableHead className="text-[11px] font-medium whitespace-nowrap">Statut</TableHead>
            <TableHead className="text-[11px] font-medium whitespace-nowrap text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {leads.map((lead) => (
            <TableRow
              key={lead.id}
              className="cursor-pointer hover:bg-muted/40 transition-colors group"
              onClick={() => onPreview(lead)}
            >
              <TableCell className="font-medium text-sm max-w-[180px] truncate">
                <div>
                  <span className="text-foreground">{lead.nom}</span>
                  {lead.hasBoamp && <BoampBadge />}
                </div>
              </TableCell>
              <TableCell><SegmentBadge segment={lead.segment} /></TableCell>
              <TableCell className="text-xs text-muted-foreground max-w-[140px] truncate">{lead.secteurActivite}</TableCell>
              <TableCell className="text-xs">{lead.ville}</TableCell>
              <TableCell className="text-xs font-mono text-muted-foreground">{lead.siren}</TableCell>
              <TableCell className="text-xs font-medium">{lead.caFormatted}</TableCell>
              <TableCell className="text-xs">{lead.nbLocaux ?? "—"}</TableCell>
              <TableCell><ScoreRing score={lead.score} /></TableCell>
              <TableCell><CompletionBar value={lead.completude} /></TableCell>
              <TableCell><StatusBadge status={lead.status} /></TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <Button
                    variant="ghost" size="icon" className="h-7 w-7"
                    onClick={(e) => { e.stopPropagation(); onNavigate(lead); }}
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    variant="ghost" size="icon" className="h-7 w-7"
                    onClick={(e) => { e.stopPropagation(); onEdit(lead); }}
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </Button>
                  <Button
                    variant="ghost" size="icon" className="h-7 w-7 hover:bg-destructive/10 hover:text-destructive"
                    onClick={(e) => { e.stopPropagation(); onDelete(lead); }}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
