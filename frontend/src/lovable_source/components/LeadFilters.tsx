import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, SlidersHorizontal, X, RotateCcw } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import type { LeadSegment, LeadStatus } from "@/types/lead";
import type { LeadFilters as Filters } from "@/hooks/use-leads";

interface Props {
  filters: Filters;
  setFilters: React.Dispatch<React.SetStateAction<Filters>>;
  activeCount: number;
  resetFilters: () => void;
  uniqueVilles: string[];
  uniqueSegments: LeadSegment[];
  uniqueStatuses: LeadStatus[];
}

export function LeadFiltersBar({
  filters, setFilters, activeCount, resetFilters, uniqueVilles, uniqueSegments, uniqueStatuses,
}: Props) {
  const [open, setOpen] = useState(false);

  const update = <K extends keyof Filters>(key: K, val: Filters[K]) =>
    setFilters((prev) => ({ ...prev, [key]: val }));

  const toggleArrayFilter = <T,>(key: keyof Filters, val: T) => {
    setFilters((prev) => {
      const arr = prev[key] as T[];
      return { ...prev, [key]: arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val] };
    });
  };

  return (
    <div className="space-y-3">
      {/* Search + toggle */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Rechercher par nom, SIREN, ville, secteur, dirigeant…"
            value={filters.search}
            onChange={(e) => update("search", e.target.value)}
            className="pl-9 h-9 text-sm"
          />
          {filters.search && (
            <button onClick={() => update("search", "")} className="absolute right-3 top-1/2 -translate-y-1/2">
              <X className="w-3.5 h-3.5 text-muted-foreground hover:text-foreground" />
            </button>
          )}
        </div>
        <Collapsible open={open} onOpenChange={setOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="outline" size="sm" className="gap-2 h-9">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              Filtres
              {activeCount > 0 && (
                <Badge className="ml-1 h-5 px-1.5 text-[10px] bg-tacir-blue text-white">{activeCount}</Badge>
              )}
            </Button>
          </CollapsibleTrigger>
        </Collapsible>
        {activeCount > 0 && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="gap-1 h-9 text-muted-foreground">
            <RotateCcw className="w-3.5 h-3.5" /> Réinitialiser
          </Button>
        )}
      </div>

      {/* Active filter chips */}
      {activeCount > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {filters.segments.map((s) => (
            <Badge key={s} variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => toggleArrayFilter("segments", s)}>
              {s} <X className="w-3 h-3" />
            </Badge>
          ))}
          {filters.statuses.map((s) => (
            <Badge key={s} variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => toggleArrayFilter("statuses", s)}>
              {s} <X className="w-3 h-3" />
            </Badge>
          ))}
          {filters.villes.map((v) => (
            <Badge key={v} variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => toggleArrayFilter("villes", v)}>
              {v} <X className="w-3 h-3" />
            </Badge>
          ))}
          {filters.hasBoamp !== null && (
            <Badge variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => update("hasBoamp", null)}>
              BOAMP: {filters.hasBoamp ? "Oui" : "Non"} <X className="w-3 h-3" />
            </Badge>
          )}
          {filters.hasEmail !== null && (
            <Badge variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => update("hasEmail", null)}>
              Email: {filters.hasEmail ? "Oui" : "Non"} <X className="w-3 h-3" />
            </Badge>
          )}
          {filters.hasTelephone !== null && (
            <Badge variant="secondary" className="gap-1 cursor-pointer text-xs" onClick={() => update("hasTelephone", null)}>
              Tél: {filters.hasTelephone ? "Oui" : "Non"} <X className="w-3 h-3" />
            </Badge>
          )}
        </div>
      )}

      {/* Expanded filters */}
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleContent>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3 p-4 rounded-xl border border-border bg-card">
            {/* Segment */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">Segment</label>
              <div className="flex flex-wrap gap-1">
                {uniqueSegments.map((s) => (
                  <Badge
                    key={s}
                    variant={filters.segments.includes(s) ? "default" : "outline"}
                    className="cursor-pointer text-[10px]"
                    onClick={() => toggleArrayFilter("segments", s)}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Statut */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">Statut</label>
              <div className="flex flex-wrap gap-1">
                {uniqueStatuses.map((s) => (
                  <Badge
                    key={s}
                    variant={filters.statuses.includes(s) ? "default" : "outline"}
                    className="cursor-pointer text-[10px]"
                    onClick={() => toggleArrayFilter("statuses", s)}
                  >
                    {s}
                  </Badge>
                ))}
              </div>
            </div>

            {/* Ville */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">Ville</label>
              <Select
                value={filters.villes[0] ?? ""}
                onValueChange={(v) => update("villes", v ? [v] : [])}
              >
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Toutes" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Toutes</SelectItem>
                  {uniqueVilles.slice(0, 30).map((v) => (
                    <SelectItem key={v} value={v}>{v}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* BOAMP */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">BOAMP</label>
              <Select
                value={filters.hasBoamp === null ? "" : filters.hasBoamp ? "true" : "false"}
                onValueChange={(v) => update("hasBoamp", v === "" ? null : v === "true")}
              >
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Tous" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tous</SelectItem>
                  <SelectItem value="true">Oui</SelectItem>
                  <SelectItem value="false">Non</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Email */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">Email</label>
              <Select
                value={filters.hasEmail === null ? "" : filters.hasEmail ? "true" : "false"}
                onValueChange={(v) => update("hasEmail", v === "" ? null : v === "true")}
              >
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Tous" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tous</SelectItem>
                  <SelectItem value="true">Avec</SelectItem>
                  <SelectItem value="false">Sans</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Téléphone */}
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-muted-foreground">Téléphone</label>
              <Select
                value={filters.hasTelephone === null ? "" : filters.hasTelephone ? "true" : "false"}
                onValueChange={(v) => update("hasTelephone", v === "" ? null : v === "true")}
              >
                <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Tous" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Tous</SelectItem>
                  <SelectItem value="true">Avec</SelectItem>
                  <SelectItem value="false">Sans</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
