import { useParams, useNavigate, Link } from "react-router-dom";
import { useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { SegmentBadge, StatusBadge, BoampBadge, ScoreRing, CompletionBar } from "@/components/leads/LeadBadges";
import { LeadEditModal } from "@/components/leads/LeadEditModal";
import {
  ArrowLeft, Building2, MapPin, Phone, Mail, Globe, Linkedin,
  Users, Calendar, FileText, BarChart3, Pencil, Trash2, RefreshCw,
  Target, TrendingUp, Activity, Clock, Database,
} from "lucide-react";
import type { UILead, UIDirigeant } from "@/types/lead";
import type { RawLeadResponse } from "@/types/lead";
import { adaptLeadResponse, formatDateFR } from "@/lib/lead-adapter";
import mockData from "@/data/mock-leads.json";
import { toast } from "sonner";

export default function LeadDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const allLeads = useMemo(() => adaptLeadResponse((mockData as RawLeadResponse).data), []);
  const lead = allLeads.find((l) => l.id === id);

  const [editOpen, setEditOpen] = useState(false);
  const [currentLead, setCurrentLead] = useState<UILead | null>(null);

  if (!lead) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg font-medium text-foreground mb-2">Lead introuvable</p>
          <Link to="/leads"><Button variant="outline" className="gap-2"><ArrowLeft className="w-4 h-4" />Retour</Button></Link>
        </div>
      </div>
    );
  }

  const displayLead = currentLead ?? lead;
  const initials = displayLead.nom.split(/\s+/).slice(0, 2).map((w) => w[0]).join("").toUpperCase();

  // Avatar colors
  const AVATAR_COLORS = [
    "bg-purple-50 text-purple-700",
    "bg-emerald-50 text-emerald-700",
    "bg-orange-50 text-orange-700",
    "bg-blue-50 text-blue-700",
    "bg-rose-50 text-rose-700",
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <header className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border">
        <div className="max-w-[1100px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/leads">
              <Button variant="ghost" size="icon" className="h-8 w-8"><ArrowLeft className="w-4 h-4" /></Button>
            </Link>
            <span className="text-sm text-muted-foreground">Mes leads / Fiche entreprise</span>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2" onClick={() => setEditOpen(true)}>
              <Pencil className="w-3.5 h-3.5" /> Modifier
            </Button>
            <Button variant="outline" size="sm" className="gap-2 hover:bg-destructive/10 hover:text-destructive">
              <Trash2 className="w-3.5 h-3.5" /> Supprimer
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-[1100px] mx-auto px-6 py-6 space-y-6">
        {/* Hero */}
        <Card className="p-6">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-xl bg-blue-50 flex items-center justify-center text-tacir-blue font-semibold text-xl flex-shrink-0">
                {initials}
              </div>
              <div>
                <h1 className="text-xl font-semibold text-foreground">{displayLead.nom}</h1>
                <p className="text-sm text-muted-foreground mt-0.5">
                  SIREN {displayLead.siren} · {displayLead.ville}, {displayLead.pays}
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  <SegmentBadge segment={displayLead.segment} />
                  <StatusBadge status={displayLead.status} />
                  {displayLead.hasBoamp && <BoampBadge />}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-center p-3 rounded-xl bg-muted/50 min-w-[70px]">
                <ScoreRing score={displayLead.score} size="md" />
                <p className="text-[10px] text-muted-foreground mt-1">Score</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-muted/50 min-w-[70px]">
                <p className="text-lg font-semibold text-foreground">{displayLead.probaConversion}%</p>
                <p className="text-[10px] text-muted-foreground">Proba.</p>
              </div>
              <div className="text-center p-3 rounded-xl bg-muted/50 min-w-[70px]">
                <p className="text-lg font-semibold text-foreground">{displayLead.completude}%</p>
                <p className="text-[10px] text-muted-foreground">Complétude</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Two-column sections */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Identité */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
                  <FileText className="w-3.5 h-3.5 text-tacir-blue" />
                </div>
                Identité
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-0">
                <InfoRow label="SIREN" value={displayLead.siren} />
                <InfoRow label="SIRET" value={displayLead.siret} />
                <InfoRow label="Identifiant" value={displayLead.identifiant} />
                <InfoRow label="Taille" value={displayLead.tailleEntreprise} badge />
                <InfoRow label="Forme juridique" value={displayLead.formeJuridique} />
                <InfoRow label="Date de création" value={displayLead.dateCreationFormatted} />
                <InfoRow label="Secteur d'activité" value={displayLead.secteurActivite} />
                <InfoRow label="Chiffre d'affaires" value={displayLead.caFormatted} highlight />
                <InfoRow label="Nb locaux" value={displayLead.nbLocaux?.toString() ?? "—"} />
              </div>
            </CardContent>
          </Card>

          {/* Adresse & Contact */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                </div>
                Adresse & contact
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-0">
                <InfoRow label="Adresse" value="Non renseigné" muted />
                <InfoRow label="Code postal" value={displayLead.codePostal} />
                <InfoRow label="Ville" value={displayLead.ville} />
                <InfoRow label="Région" value="Non renseigné" muted />
                <InfoRow label="Pays" value={displayLead.pays} />
                <InfoRow label="Email" value={displayLead.email} link />
                <InfoRow label="Téléphone" value={displayLead.telephone} link />
                <InfoRow label="Site web" value="Non renseigné" muted />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Dirigeants */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center">
                <Users className="w-3.5 h-3.5 text-purple-600" />
              </div>
              Dirigeants & contacts ({displayLead.nbDirigeants})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {displayLead.dirigeants.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">Aucun dirigeant renseigné</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {displayLead.dirigeants.map((d, i) => (
                  <DirigeantCard key={d.id} dirigeant={d} colorClass={AVATAR_COLORS[i % AVATAR_COLORS.length]} />
                ))}
              </div>
            )}
            {/* Completude contacts */}
            <div className="flex items-center gap-3 mt-4 pt-4 border-t border-border">
              <span className="text-[11px] text-muted-foreground">Complétude contacts</span>
              <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500"
                  style={{ width: `${Math.min(100, displayLead.dirigeants.filter((d) => d.linkedinUrl).length / Math.max(1, displayLead.nbDirigeants) * 100)}%` }}
                />
              </div>
              <span className="text-xs font-medium text-emerald-600">
                {Math.round(displayLead.dirigeants.filter((d) => d.linkedinUrl).length / Math.max(1, displayLead.nbDirigeants) * 100)}%
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Indicateurs métier */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center">
                <BarChart3 className="w-3.5 h-3.5 text-amber-600" />
              </div>
              Indicateurs métier
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Metric icon={Target} label="Score" value={`${displayLead.score}/100`} />
              <Metric icon={TrendingUp} label="Proba. conversion" value={`${displayLead.probaConversion}%`} />
              <Metric icon={Activity} label="Complétude" value={`${displayLead.completude}%`} />
              <Metric icon={Users} label="Nb dirigeants" value={`${displayLead.nbDirigeants}`} />
              <Metric icon={Linkedin} label="LinkedIn" value={displayLead.hasLinkedinDirigeant ? "Oui" : "Non"} />
              <Metric icon={Mail} label="Email" value={displayLead.hasEmail ? "Oui" : "Non"} />
              <Metric icon={Phone} label="Téléphone" value={displayLead.hasTelephone ? "Oui" : "Non"} />
              <Metric icon={Clock} label="Fraîcheur" value={displayLead.dateScrapingFormatted} />
            </div>
          </CardContent>
        </Card>

        {/* Métadonnées */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold flex items-center gap-2 text-muted-foreground">
              <div className="w-7 h-7 rounded-lg bg-muted flex items-center justify-center">
                <Database className="w-3.5 h-3.5 text-muted-foreground" />
              </div>
              Métadonnées & source
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-0">
              <InfoRow label="Date création entreprise" value={displayLead.dateCreationFormatted} />
              <InfoRow label="Dernière modif. site" value={displayLead.dateDerniereModifFormatted} />
              <InfoRow label="Date scraping" value={displayLead.dateScrapingFormatted} />
              <InfoRow label="Créé le" value={displayLead.createdAt ? formatDateFR(displayLead.createdAt) : "—"} />
              <InfoRow label="Mis à jour le" value={displayLead.updatedAt ? formatDateFR(displayLead.updatedAt) : "—"} />
              <InfoRow label="Raw Lead ID" value={displayLead.rawLeadId ?? "—"} />
            </div>
            {displayLead.sources && (
              <div className="mt-3 pt-3 border-t border-border">
                <p className="text-[11px] text-muted-foreground mb-1">Sources</p>
                <p className="text-xs font-mono text-muted-foreground bg-muted/50 rounded-lg p-2 overflow-x-auto">
                  {JSON.stringify(displayLead.sources, null, 0).slice(0, 200)}…
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Action buttons */}
        <div className="flex justify-end gap-3 pb-8">
          <Button variant="outline" className="gap-2">
            <RefreshCw className="w-3.5 h-3.5" /> Prospects similaires
          </Button>
          <Button className="gap-2">
            <TrendingUp className="w-3.5 h-3.5" /> Analyser le potentiel
          </Button>
        </div>
      </main>

      <LeadEditModal
        lead={editOpen ? displayLead : null}
        open={editOpen}
        onClose={() => setEditOpen(false)}
        onSave={(id, updates) => {
          setCurrentLead({ ...displayLead, ...updates } as UILead);
          toast.success("Lead mis à jour");
        }}
      />
    </div>
  );
}

// ---- Sub-components ----

function InfoRow({ label, value, link, highlight, muted, badge }: {
  label: string; value: string; link?: boolean; highlight?: boolean; muted?: boolean; badge?: boolean;
}) {
  const isMissing = value === "—" || value === "Non renseigné";
  return (
    <div className="flex items-center justify-between py-2 border-b border-border last:border-b-0">
      <span className="text-[11px] text-muted-foreground">{label}</span>
      {badge ? (
        <Badge variant="outline" className="text-[10px] bg-blue-50 text-tacir-blue border-blue-200">{value}</Badge>
      ) : (
        <span className={`text-xs font-medium text-right max-w-[200px] truncate ${
          isMissing || muted ? "text-muted-foreground italic" :
          link ? "text-tacir-blue" :
          highlight ? "text-emerald-600" :
          "text-foreground"
        }`}>
          {value}
        </span>
      )}
    </div>
  );
}

function DirigeantCard({ dirigeant, colorClass }: { dirigeant: UIDirigeant; colorClass: string }) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl bg-muted/40 hover:bg-muted/60 transition-colors">
      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 ${colorClass}`}>
        {dirigeant.initials}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">{dirigeant.fullName}</p>
        <p className="text-[11px] text-muted-foreground">{dirigeant.qualite}</p>
        <div className="flex items-center gap-3 mt-1.5 flex-wrap">
          <span className="text-[11px] text-muted-foreground italic">Email non renseigné</span>
          <span className="text-[11px] text-muted-foreground italic">Tél. non renseigné</span>
        </div>
      </div>
      <div className="flex flex-col items-end gap-1 flex-shrink-0">
        {dirigeant.age && (
          <div className="text-center">
            <span className="text-base font-semibold text-foreground">{dirigeant.age}</span>
            <span className="text-[10px] text-muted-foreground block">ans</span>
          </div>
        )}
        {dirigeant.linkedinUrl && (
          <a href={dirigeant.linkedinUrl} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800">
            <Linkedin className="w-4 h-4" />
          </a>
        )}
      </div>
    </div>
  );
}

function Metric({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="p-3 rounded-xl bg-muted/40 text-center">
      <Icon className="w-4 h-4 text-muted-foreground mx-auto mb-1" />
      <p className="text-sm font-semibold text-foreground">{value}</p>
      <p className="text-[10px] text-muted-foreground">{label}</p>
    </div>
  );
}
