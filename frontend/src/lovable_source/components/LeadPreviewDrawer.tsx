import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { SegmentBadge, StatusBadge, BoampBadge, ScoreRing, CompletionBar } from "./LeadBadges";
import { Eye, Pencil, Trash2, MapPin, Phone, Mail, Linkedin, Building2, Users } from "lucide-react";
import type { UILead } from "@/types/lead";

interface Props {
  lead: UILead | null;
  open: boolean;
  onClose: () => void;
  onNavigate: (lead: UILead) => void;
  onEdit: (lead: UILead) => void;
  onDelete: (lead: UILead) => void;
}

export function LeadPreviewDrawer({ lead, open, onClose, onNavigate, onEdit, onDelete }: Props) {
  if (!lead) return null;

  const initials = lead.nom
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-[420px] sm:w-[460px] overflow-y-auto p-0">
        <SheetHeader className="p-5 pb-0">
          <div className="flex items-start gap-3">
            <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center text-tacir-blue font-semibold text-base flex-shrink-0">
              {initials}
            </div>
            <div className="flex-1 min-w-0">
              <SheetTitle className="text-base font-semibold text-foreground truncate">{lead.nom}</SheetTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                SIREN {lead.siren} · {lead.ville}, {lead.pays}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                <SegmentBadge segment={lead.segment} />
                <StatusBadge status={lead.status} />
                {lead.hasBoamp && <BoampBadge />}
              </div>
            </div>
          </div>
        </SheetHeader>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-3 p-5">
          <div className="text-center p-3 rounded-xl bg-muted/50">
            <ScoreRing score={lead.score} size="md" />
            <p className="text-[10px] text-muted-foreground mt-1">Score</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-muted/50">
            <p className="text-lg font-semibold text-foreground">{lead.probaConversion}%</p>
            <p className="text-[10px] text-muted-foreground">Proba.</p>
          </div>
          <div className="text-center p-3 rounded-xl bg-muted/50">
            <p className="text-lg font-semibold text-foreground">{lead.completude}%</p>
            <p className="text-[10px] text-muted-foreground">Complétude</p>
          </div>
        </div>

        <Separator />

        {/* Info */}
        <div className="p-5 space-y-3">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Informations</h4>
          <div className="space-y-2 text-sm">
            <Row icon={Building2} label="Secteur" value={lead.secteurActivite} />
            <Row icon={Building2} label="Forme juridique" value={lead.formeJuridique} />
            <Row icon={Building2} label="CA" value={lead.caFormatted} />
            <Row icon={MapPin} label="Ville" value={`${lead.ville} (${lead.codePostal})`} />
            <Row icon={Phone} label="Téléphone" value={lead.telephone} />
            <Row icon={Mail} label="Email" value={lead.email} />
          </div>
        </div>

        <Separator />

        {/* Dirigeants */}
        <div className="p-5 space-y-3">
          <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
            <Users className="w-3.5 h-3.5" /> Dirigeants ({lead.nbDirigeants})
          </h4>
          {lead.dirigeants.slice(0, 4).map((d) => (
            <div key={d.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted/40">
              <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-700 flex items-center justify-center text-[11px] font-semibold flex-shrink-0">
                {d.initials}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{d.fullName}</p>
                <p className="text-[11px] text-muted-foreground">{d.qualite}</p>
              </div>
              <div className="flex items-center gap-1">
                {d.age && <span className="text-xs text-muted-foreground">{d.age} ans</span>}
                {d.linkedinUrl && (
                  <a href={d.linkedinUrl} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>
                    <Linkedin className="w-3.5 h-3.5 text-blue-600" />
                  </a>
                )}
              </div>
            </div>
          ))}
          {lead.nbDirigeants > 4 && (
            <p className="text-xs text-muted-foreground text-center">
              +{lead.nbDirigeants - 4} autres dirigeants
            </p>
          )}
        </div>

        <Separator />

        {/* Actions */}
        <div className="p-5 flex flex-col gap-2">
          <Button className="w-full gap-2" onClick={() => onNavigate(lead)}>
            <Eye className="w-4 h-4" /> Voir la fiche complète
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" className="flex-1 gap-2" onClick={() => onEdit(lead)}>
              <Pencil className="w-3.5 h-3.5" /> Modifier
            </Button>
            <Button variant="outline" className="gap-2 hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30" onClick={() => onDelete(lead)}>
              <Trash2 className="w-3.5 h-3.5" /> Supprimer
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function Row({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
      <span className="text-muted-foreground text-xs w-28 flex-shrink-0">{label}</span>
      <span className={`text-xs font-medium truncate ${value === "—" ? "text-muted-foreground italic" : "text-foreground"}`}>
        {value}
      </span>
    </div>
  );
}
