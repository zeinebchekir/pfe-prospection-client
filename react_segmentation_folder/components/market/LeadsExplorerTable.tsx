import { useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EXPLORER_LEADS, SEGMENTS, formatRevenue } from "@/lib/segments-data";
import type { ExplorerLead, MarketSegment } from "@/lib/segments-data";

const ALL = "__all__";

export function LeadsExplorerTable() {
  const [search, setSearch] = useState("");
  const [segmentFilter, setSegmentFilter] = useState(ALL);
  const [regionFilter, setRegionFilter] = useState(ALL);
  const [sectorFilter, setSectorFilter] = useState(ALL);
  const [categoryFilter, setCategoryFilter] = useState(ALL);
  const [revenueFilter, setRevenueFilter] = useState(ALL);

  const segmentMap = useMemo(() => {
    const map = new Map<string, MarketSegment>();
    SEGMENTS.forEach((s) => map.set(s.id, s));
    return map;
  }, []);

  const regions = useMemo(() => Array.from(new Set(EXPLORER_LEADS.map((l) => l.region))).sort(), []);
  const sectors = useMemo(() => Array.from(new Set(EXPLORER_LEADS.map((l) => l.secteur))).sort(), []);
  const categories = useMemo(() => Array.from(new Set(EXPLORER_LEADS.map((l) => l.categorie))).sort(), []);

  const filtered = useMemo(() => {
    return EXPLORER_LEADS.filter((l) => {
      if (segmentFilter !== ALL && l.segmentId !== segmentFilter) return false;
      if (regionFilter !== ALL && l.region !== regionFilter) return false;
      if (sectorFilter !== ALL && l.secteur !== sectorFilter) return false;
      if (categoryFilter !== ALL && l.categorie !== categoryFilter) return false;
      if (revenueFilter !== ALL) {
        const ca = l.ca ?? 0;
        if (revenueFilter === "lt1m" && ca >= 1_000_000) return false;
        if (revenueFilter === "1m-100m" && (ca < 1_000_000 || ca >= 100_000_000)) return false;
        if (revenueFilter === "100m-1b" && (ca < 100_000_000 || ca >= 1_000_000_000)) return false;
        if (revenueFilter === "gt1b" && ca < 1_000_000_000) return false;
      }
      if (search) {
        const q = search.toLowerCase();
        if (
          !l.nom.toLowerCase().includes(q) &&
          !l.ville.toLowerCase().includes(q) &&
          !l.siren.includes(q) &&
          !l.secteur.toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    });
  }, [search, segmentFilter, regionFilter, sectorFilter, categoryFilter, revenueFilter]);

  const activeFilters =
    (segmentFilter !== ALL ? 1 : 0) +
    (regionFilter !== ALL ? 1 : 0) +
    (sectorFilter !== ALL ? 1 : 0) +
    (categoryFilter !== ALL ? 1 : 0) +
    (revenueFilter !== ALL ? 1 : 0) +
    (search ? 1 : 0);

  const reset = () => {
    setSearch("");
    setSegmentFilter(ALL);
    setRegionFilter(ALL);
    setSectorFilter(ALL);
    setCategoryFilter(ALL);
    setRevenueFilter(ALL);
  };

  return (
    <Card className="p-5 rounded-xl">
      <div className="flex items-start justify-between mb-4 flex-wrap gap-3">
        <div>
          <h3 className="font-semibold text-foreground text-sm">Explorateur de leads</h3>
          <p className="text-xs text-muted-foreground">
            {filtered.length} lead{filtered.length > 1 ? "s" : ""} affiché{filtered.length > 1 ? "s" : ""}
          </p>
        </div>
        {activeFilters > 0 && (
          <Button variant="ghost" size="sm" onClick={reset} className="h-8 text-xs">
            <X className="w-3 h-3 mr-1" /> Réinitialiser ({activeFilters})
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 mb-4">
        <div className="relative col-span-2 lg:col-span-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-9 text-sm"
          />
        </div>
        <Select value={segmentFilter} onValueChange={setSegmentFilter}>
          <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="Segment" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tous segments</SelectItem>
            {SEGMENTS.map((s) => (
              <SelectItem key={s.id} value={s.id}>{s.shortName}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={regionFilter} onValueChange={setRegionFilter}>
          <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="Région" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Toutes régions</SelectItem>
            {regions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={sectorFilter} onValueChange={setSectorFilter}>
          <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="Secteur" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tous secteurs</SelectItem>
            {sectors.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="Catégorie" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Toutes catégories</SelectItem>
            {categories.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={revenueFilter} onValueChange={setRevenueFilter}>
          <SelectTrigger className="h-9 text-xs"><SelectValue placeholder="CA" /></SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL}>Tous CA</SelectItem>
            <SelectItem value="lt1m">{"< 1 M€"}</SelectItem>
            <SelectItem value="1m-100m">1 – 100 M€</SelectItem>
            <SelectItem value="100m-1b">100 M€ – 1 Md€</SelectItem>
            <SelectItem value="gt1b">{"> 1 Md€"}</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="border rounded-lg overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent bg-muted/30">
              <TableHead className="text-[11px] font-semibold">Entreprise</TableHead>
              <TableHead className="text-[11px] font-semibold">Segment</TableHead>
              <TableHead className="text-[11px] font-semibold">Secteur</TableHead>
              <TableHead className="text-[11px] font-semibold">Ville</TableHead>
              <TableHead className="text-[11px] font-semibold">SIREN</TableHead>
              <TableHead className="text-[11px] font-semibold text-right">CA</TableHead>
              <TableHead className="text-[11px] font-semibold text-right">Âge</TableHead>
              <TableHead className="text-[11px] font-semibold">Région</TableHead>
              <TableHead className="text-[11px] font-semibold">Catégorie</TableHead>
              <TableHead className="text-[11px] font-semibold">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((lead) => {
              const seg = segmentMap.get(lead.segmentId);
              return (
                <ExplorerRow key={lead.id} lead={lead} segment={seg} />
              );
            })}
            {filtered.length === 0 && (
              <TableRow>
                <TableCell colSpan={10} className="text-center text-sm text-muted-foreground py-12">
                  Aucun lead ne correspond aux filtres.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}

function ExplorerRow({ lead, segment }: { lead: ExplorerLead; segment?: MarketSegment }) {
  return (
    <TableRow className="hover:bg-muted/30">
      <TableCell className="text-xs font-medium max-w-[200px] truncate">{lead.nom}</TableCell>
      <TableCell>
        {segment && (
          <span
            className="text-[10px] font-semibold px-2 py-0.5 rounded-full inline-block"
            style={{ backgroundColor: `${segment.color}1A`, color: segment.color }}
          >
            {segment.shortName}
          </span>
        )}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground max-w-[140px] truncate">{lead.secteur}</TableCell>
      <TableCell className="text-xs">{lead.ville}</TableCell>
      <TableCell className="text-xs font-mono text-muted-foreground">{lead.siren}</TableCell>
      <TableCell className="text-xs font-medium text-right">{formatRevenue(lead.ca)}</TableCell>
      <TableCell className="text-xs text-right">{lead.age} ans</TableCell>
      <TableCell className="text-xs">{lead.region}</TableCell>
      <TableCell className="text-xs text-muted-foreground max-w-[160px] truncate">{lead.categorie}</TableCell>
      <TableCell>
        <Badge variant="outline" className="text-[10px] font-medium">{lead.action}</Badge>
      </TableCell>
    </TableRow>
  );
}
