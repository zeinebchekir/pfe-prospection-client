import { useMemo } from "react";
import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, CheckCircle2, Calendar } from "lucide-react";
import { MarketKPICards } from "@/components/market/MarketKPICards";
import { SegmentBubbleChart } from "@/components/market/SegmentBubbleChart";
import { SegmentCard } from "@/components/market/SegmentCard";
import { SegmentComparisonCharts } from "@/components/market/SegmentComparisonCharts";
import { SegmentRadarChart } from "@/components/market/SegmentRadarChart";
import { OpportunityMatrix } from "@/components/market/OpportunityMatrix";
import { LeadsExplorerTable } from "@/components/market/LeadsExplorerTable";
import { InsightsPanel } from "@/components/market/InsightsPanel";
import { SEGMENTS, TOTAL_LEADS, formatRevenue } from "@/lib/segments-data";

export default function MarketAnalysisPage() {
  const kpis = useMemo(() => {
    const dominant = [...SEGMENTS].sort((a, b) => b.count - a.count)[0];
    const totalLeadsWithCA = SEGMENTS.reduce((sum, s) => sum + s.count, 0);
    const weightedRevenue = SEGMENTS.reduce((sum, s) => sum + s.avgRevenue * s.count, 0) / totalLeadsWithCA;
    const weightedAge = SEGMENTS.reduce((sum, s) => sum + s.avgAge * s.count, 0) / totalLeadsWithCA;
    // Priority: highest avg revenue × count score
    const priority = [...SEGMENTS].sort((a, b) => b.avgRevenue * b.count - a.avgRevenue * a.count)[0];

    return {
      totalLeads: TOTAL_LEADS,
      segmentsCount: SEGMENTS.length,
      dominantSegment: dominant.shortName,
      avgRevenue: formatRevenue(Math.round(weightedRevenue)),
      avgAge: weightedAge.toFixed(1),
      prioritySegment: priority.shortName,
    };
  }, []);

  const today = new Date().toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="min-h-screen bg-background">
      {/* Sticky header */}
      <header className="sticky top-0 z-30 bg-background/80 backdrop-blur-md border-b">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-4">
            <Link to="/dashboard">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-xl font-bold text-foreground tracking-tight">
                Analyse de marché & segmentation
              </h1>
              <p className="text-xs text-muted-foreground">
                Vue exécutive des segments de leads issus de l'analyse de clustering
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Calendar className="w-3.5 h-3.5" />
              <span>{today}</span>
            </div>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-full bg-tacir-green/10 text-tacir-green border border-tacir-green/20">
              <CheckCircle2 className="w-3 h-3" />
              Données à jour
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        {/* SECTION B - KPI cards */}
        <section>
          <MarketKPICards {...kpis} />
        </section>

        {/* SECTION C - Bubble chart hero */}
        <section>
          <Card className="p-5 rounded-xl">
            <div className="mb-4 flex items-start justify-between flex-wrap gap-2">
              <div>
                <h2 className="font-semibold text-foreground text-sm">Vue synthétique des segments</h2>
                <p className="text-xs text-muted-foreground">
                  Taille des bulles = volume de leads · couleur = segment
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {SEGMENTS.map((s) => (
                  <div key={s.id} className="flex items-center gap-1.5 text-[11px]">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                    <span className="text-muted-foreground">{s.shortName}</span>
                  </div>
                ))}
              </div>
            </div>
            <SegmentBubbleChart segments={SEGMENTS} total={TOTAL_LEADS} />
          </Card>
        </section>

        {/* SECTION D - Segment cards */}
        <section>
          <div className="mb-3">
            <h2 className="font-semibold text-foreground text-sm">Profils des segments</h2>
            <p className="text-xs text-muted-foreground">Caractéristiques métier et recommandations</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {SEGMENTS.map((s) => (
              <SegmentCard key={s.id} segment={s} />
            ))}
          </div>
        </section>

        {/* SECTION E - Comparative charts */}
        <section>
          <SegmentComparisonCharts segments={SEGMENTS} />
        </section>

        {/* SECTION F + G - Radar + Matrix */}
        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SegmentRadarChart segments={SEGMENTS} />
          <OpportunityMatrix segments={SEGMENTS} />
        </section>

        {/* SECTION I - Insights */}
        <section>
          <InsightsPanel />
        </section>

        {/* SECTION H - Leads explorer */}
        <section>
          <LeadsExplorerTable />
        </section>
      </main>
    </div>
  );
}
