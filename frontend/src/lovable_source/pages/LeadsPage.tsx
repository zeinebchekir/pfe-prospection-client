import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Building2, ArrowLeft } from "lucide-react";
import { useLeads } from "@/hooks/use-leads";
import { LeadKPICards } from "@/components/leads/LeadKPICards";
import { LeadFiltersBar } from "@/components/leads/LeadFilters";
import { LeadTable } from "@/components/leads/LeadTable";
import { LeadPagination } from "@/components/leads/LeadPagination";
import { LeadPreviewDrawer } from "@/components/leads/LeadPreviewDrawer";
import { LeadEditModal } from "@/components/leads/LeadEditModal";
import type { UILead } from "@/types/lead";
import { toast } from "sonner";
import { Link } from "react-router-dom";

export default function LeadsPage() {
  const navigate = useNavigate();
  const {
    paginatedLeads, filters, setFilters, sortField, sortDir, toggleSort,
    page, setPage, pageSize, totalPages, kpis, uniqueVilles, uniqueSegments,
    uniqueStatuses, activeFilterCount, resetFilters, updateLead, filteredLeads,
  } = useLeads();

  const [previewLead, setPreviewLead] = useState<UILead | null>(null);
  const [editLead, setEditLead] = useState<UILead | null>(null);

  const handleNavigate = (lead: UILead) => {
    navigate(`/leads/${lead.id}`);
  };

  const handleDelete = (lead: UILead) => {
    toast.info(`Suppression de ${lead.nom} (simulation)`);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top bar */}
      <header className="sticky top-0 z-30 bg-background/95 backdrop-blur border-b border-border">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link to="/">
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <ArrowLeft className="w-4 h-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <Building2 className="w-5 h-5 text-tacir-blue" />
                Mes leads
              </h1>
              <p className="text-xs text-muted-foreground">
                Gérez et qualifiez votre portefeuille de prospects B2B
              </p>
            </div>
          </div>
          <Button className="gap-2">
            <Plus className="w-4 h-4" /> Nouveau lead
          </Button>
        </div>
      </header>

      <main className="max-w-[1400px] mx-auto px-6 py-6 space-y-6">
        {/* KPIs */}
        <LeadKPICards kpis={kpis} />

        {/* Filters */}
        <LeadFiltersBar
          filters={filters}
          setFilters={setFilters}
          activeCount={activeFilterCount}
          resetFilters={resetFilters}
          uniqueVilles={uniqueVilles}
          uniqueSegments={uniqueSegments}
          uniqueStatuses={uniqueStatuses}
        />

        {/* Table */}
        <Card className="overflow-hidden">
          <LeadTable
            leads={paginatedLeads}
            sortField={sortField}
            sortDir={sortDir}
            onSort={toggleSort}
            onPreview={setPreviewLead}
            onEdit={setEditLead}
            onDelete={handleDelete}
            onNavigate={handleNavigate}
          />
          <div className="px-4 pb-4">
            <LeadPagination
              page={page}
              totalPages={totalPages}
              totalItems={filteredLeads.length}
              pageSize={pageSize}
              onPageChange={setPage}
            />
          </div>
        </Card>
      </main>

      {/* Drawer */}
      <LeadPreviewDrawer
        lead={previewLead}
        open={previewLead !== null}
        onClose={() => setPreviewLead(null)}
        onNavigate={handleNavigate}
        onEdit={(l) => { setPreviewLead(null); setEditLead(l); }}
        onDelete={handleDelete}
      />

      {/* Edit Modal */}
      <LeadEditModal
        lead={editLead}
        open={editLead !== null}
        onClose={() => setEditLead(null)}
        onSave={(id, updates) => updateLead(id, updates)}
      />
    </div>
  );
}
