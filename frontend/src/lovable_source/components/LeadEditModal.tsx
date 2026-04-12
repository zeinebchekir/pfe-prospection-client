import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Users } from "lucide-react";
import type { UILead, LeadStatus } from "@/types/lead";
import { toast } from "sonner";

interface Props {
  lead: UILead | null;
  open: boolean;
  onClose: () => void;
  onSave: (id: string, updates: Partial<UILead>) => void;
}

export function LeadEditModal({ lead, open, onClose, onSave }: Props) {
  const [form, setForm] = useState({
    nom: "",
    siren: "",
    siret: "",
    identifiant: "",
    segment: "",
    tailleEntreprise: "",
    secteurActivite: "",
    formeJuridique: "",
    ville: "",
    codePostal: "",
    pays: "",
    caFormatted: "",
    telephone: "",
    email: "",
    status: "Nouveau" as LeadStatus,
    notes: "",
  });

  useEffect(() => {
    if (lead) {
      setForm({
        nom: lead.nom === "—" ? "" : lead.nom,
        siren: lead.siren === "—" ? "" : lead.siren,
        siret: lead.siret === "—" ? "" : lead.siret,
        identifiant: lead.identifiant === "—" ? "" : lead.identifiant,
        segment: lead.segment,
        tailleEntreprise: lead.tailleEntreprise === "—" ? "" : lead.tailleEntreprise,
        secteurActivite: lead.secteurActivite === "—" ? "" : lead.secteurActivite,
        formeJuridique: lead.formeJuridique === "—" ? "" : lead.formeJuridique,
        ville: lead.ville === "—" ? "" : lead.ville,
        codePostal: lead.codePostal === "—" ? "" : lead.codePostal,
        pays: lead.pays === "—" ? "" : lead.pays,
        caFormatted: lead.caFormatted === "—" ? "" : lead.caFormatted,
        telephone: lead.telephone === "—" ? "" : lead.telephone,
        email: lead.email === "—" ? "" : lead.email,
        status: lead.status,
        notes: "",
      });
    }
  }, [lead]);

  if (!lead) return null;

  const handleSave = () => {
    onSave(lead.id, {
      nom: form.nom || "—",
      siren: form.siren || "—",
      siret: form.siret || "—",
      identifiant: form.identifiant || "—",
      ville: form.ville || "—",
      codePostal: form.codePostal || "—",
      pays: form.pays || "—",
      telephone: form.telephone || "—",
      email: form.email || "—",
      status: form.status,
    });
    toast.success("Lead mis à jour avec succès");
    onClose();
  };

  const update = (key: string, val: string) => setForm((p) => ({ ...p, [key]: val }));

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[85vh] p-0">
        <DialogHeader className="p-6 pb-0">
          <DialogTitle className="text-lg font-semibold">Modifier le lead — {lead.nom}</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="general" className="px-6">
          <TabsList className="mb-4">
            <TabsTrigger value="general" className="text-xs">Informations</TabsTrigger>
            <TabsTrigger value="contact" className="text-xs">Contact</TabsTrigger>
            <TabsTrigger value="dirigeants" className="text-xs">Dirigeants</TabsTrigger>
          </TabsList>

          <ScrollArea className="max-h-[50vh]">
            <TabsContent value="general" className="space-y-4 pr-4">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Nom de l'entreprise" value={form.nom} onChange={(v) => update("nom", v)} />
                <Field label="SIREN" value={form.siren} onChange={(v) => update("siren", v)} />
                <Field label="SIRET" value={form.siret} onChange={(v) => update("siret", v)} />
                <Field label="Identifiant" value={form.identifiant} onChange={(v) => update("identifiant", v)} />
                <Field label="Taille entreprise" value={form.tailleEntreprise} onChange={(v) => update("tailleEntreprise", v)} disabled />
                <Field label="Secteur d'activité" value={form.secteurActivite} onChange={(v) => update("secteurActivite", v)} />
                <Field label="Forme juridique" value={form.formeJuridique} onChange={(v) => update("formeJuridique", v)} />
                <Field label="CA" value={form.caFormatted} onChange={(v) => update("caFormatted", v)} disabled />
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">Statut</Label>
                <Select value={form.status} onValueChange={(v) => update("status", v)}>
                  <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Nouveau">Nouveau</SelectItem>
                    <SelectItem value="Qualifié">Qualifié</SelectItem>
                    <SelectItem value="Opportunité">Opportunité</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs font-medium text-muted-foreground">Notes internes</Label>
                <Textarea
                  placeholder="Ajouter des notes…"
                  value={form.notes}
                  onChange={(e) => update("notes", e.target.value)}
                  className="min-h-[80px] text-sm"
                />
              </div>
            </TabsContent>

            <TabsContent value="contact" className="space-y-4 pr-4">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Ville" value={form.ville} onChange={(v) => update("ville", v)} />
                <Field label="Code postal" value={form.codePostal} onChange={(v) => update("codePostal", v)} />
                <Field label="Pays" value={form.pays} onChange={(v) => update("pays", v)} />
                <Field label="Téléphone" value={form.telephone} onChange={(v) => update("telephone", v)} />
                <Field label="Email" value={form.email} onChange={(v) => update("email", v)} type="email" />
              </div>
            </TabsContent>

            <TabsContent value="dirigeants" className="space-y-3 pr-4">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Users className="w-3.5 h-3.5" />
                {lead.nbDirigeants} dirigeant{lead.nbDirigeants > 1 ? "s" : ""} (lecture seule)
              </p>
              {lead.dirigeants.map((d) => (
                <div key={d.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/40">
                  <div className="w-8 h-8 rounded-full bg-purple-50 text-purple-700 flex items-center justify-center text-[11px] font-semibold">
                    {d.initials}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{d.fullName}</p>
                    <p className="text-[11px] text-muted-foreground">{d.qualite}</p>
                  </div>
                </div>
              ))}
            </TabsContent>
          </ScrollArea>
        </Tabs>

        <Separator />

        <DialogFooter className="p-6 pt-4">
          <Button variant="outline" onClick={onClose}>Annuler</Button>
          <Button onClick={handleSave}>Enregistrer</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Field({ label, value, onChange, disabled, type = "text" }: {
  label: string; value: string; onChange: (v: string) => void; disabled?: boolean; type?: string;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-[11px] font-medium text-muted-foreground">{label}</Label>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="h-9 text-sm"
      />
    </div>
  );
}
