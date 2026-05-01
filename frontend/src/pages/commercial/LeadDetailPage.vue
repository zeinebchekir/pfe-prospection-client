<template>
  <div>
    <div class="flex min-h-screen bg-tacir-lightgray/30">

    <!-- Sidebar -->
    <TheSidebar />

    <!-- Main content -->
    <div class="flex-1 flex flex-col min-w-0">

      <!-- Header -->
      <header class="h-14 sm:h-16 border-b border-border bg-white sticky top-0 z-40 px-3 sm:px-6 flex items-center justify-between shadow-sm">
        <div class="flex items-center gap-2 sm:gap-3 min-w-0">
          <button
            @click="router.push('/commercial/leads')"
            class="w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-lg hover:bg-tacir-lightgray text-tacir-darkgray transition-colors"
          >
            <ArrowLeft class="h-4 w-4" />
          </button>
          <span class="text-xs sm:text-sm text-muted-foreground truncate hidden xs:block sm:block">Mes leads / Fiche entreprise</span>
        </div>
        <div class="flex items-center gap-1.5 sm:gap-2 flex-shrink-0">
          <button
            @click="editOpen = true"
            class="inline-flex items-center gap-1.5 h-8 px-2 sm:px-3 text-sm rounded-md border border-input hover:bg-accent transition-colors"
          >
            <Pencil class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Modifier</span>
          </button>
          <button
            class="inline-flex items-center gap-1.5 h-8 px-2 sm:px-3 text-sm rounded-md border border-input hover:bg-destructive/10 hover:text-destructive transition-colors"
          >
            <Trash2 class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">Supprimer</span>
          </button>
        </div>
      </header>

      <!-- Loading / Lead not found -->
      <div v-if="!displayLead" class="flex-1 flex items-center justify-center">
        <div v-if="isLoading" class="text-center space-y-3 flex flex-col items-center">
          <Loader2 class="h-8 w-8 animate-spin text-tacir-blue" />
          <p class="text-sm font-medium text-muted-foreground">Chargement...</p>
        </div>
        <div v-else class="text-center space-y-3">
          <p class="text-lg font-medium text-foreground">Lead introuvable</p>
          <button
            @click="router.push('/commercial/leads')"
            class="inline-flex items-center gap-2 h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors"
          >
            <ArrowLeft class="w-4 h-4" /> Retour à la liste
          </button>
        </div>
      </div>

      <!-- Lead detail -->
      <main v-else class="flex-1 p-6 md:p-8 overflow-y-auto">
        <div class="max-w-[1100px] mx-auto space-y-6">

          <!-- Hero card -->
          <div class="bg-white rounded-xl border border-border shadow-card p-4 sm:p-6">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div class="flex items-center gap-3 sm:gap-4">
                <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-blue-50 flex items-center justify-center text-tacir-blue font-semibold text-lg sm:text-xl flex-shrink-0">
                  {{ initials }}
                </div>
                <div class="min-w-0">
                  <h1 class="text-lg sm:text-xl font-semibold text-foreground truncate">{{ displayLead.nom }}</h1>
                  <p class="text-xs sm:text-sm text-muted-foreground mt-0.5">
                    SIREN {{ displayLead.siren }} · {{ displayLead.ville }}, {{ displayLead.pays }}
                  </p>
                  <div class="flex flex-wrap gap-1.5 mt-2">
                    <SegmentBadge :segment="displayLead.segment" />
                    <StatusBadge  :status="displayLead.status"  />
                    <span
                      v-if="displayLead.hasBoamp"
                      class="text-[10px] font-semibold px-2 py-0.5 rounded-sm bg-blue-50 text-tacir-blue border border-blue-200"
                    >
                      BOAMP
                    </span>
                  </div>
                </div>
              </div>
              <!-- Metric chips — wrap naturally on mobile -->
              <div class="flex items-center gap-2 sm:gap-4 flex-wrap">
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <ScoreRing :score="displayLead.score" size="md" />
                  <p class="text-[10px] text-muted-foreground mt-1">Score</p>
                </div>
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <p class="text-base sm:text-lg font-semibold text-foreground">{{ displayLead.probaConversion }}%</p>
                  <p class="text-[10px] text-muted-foreground">Proba.</p>
                </div>
                <div class="text-center p-2.5 sm:p-3 rounded-xl bg-muted/50 min-w-[64px] sm:min-w-[70px]">
                  <p class="text-base sm:text-lg font-semibold text-foreground">{{ displayLead.completude }}%</p>
                  <p class="text-[10px] text-muted-foreground">Complétude</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Two-column detail -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Identité -->
            <div class="bg-white rounded-xl border border-border shadow-card p-5">
              <div class="flex items-center gap-2 mb-4">
                <div class="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center">
                  <FileText class="w-3.5 h-3.5 text-tacir-blue" />
                </div>
                <h2 class="text-sm font-semibold">Identité</h2>
              </div>
              <InfoRow label="SIREN"              :value="displayLead.siren" />
              <InfoRow label="SIRET"              :value="displayLead.siret" />
              <InfoRow label="Identifiant"        :value="displayLead.identifiant" />
              <InfoRow label="Taille"             :value="displayLead.tailleEntreprise" badge />
              <InfoRow label="Forme juridique"    :value="displayLead.formeJuridique" />
              <InfoRow label="Date de création"   :value="displayLead.dateCreationFormatted" />
              <InfoRow label="Secteur d'activité" :value="displayLead.secteurActivite" />
              <InfoRow label="Chiffre d'affaires" :value="displayLead.caFormatted" highlight />
              <InfoRow label="Nb locaux"          :value="displayLead.nbLocaux?.toString() ?? '—'" />
            </div>

            <!-- Adresse & Contact -->
            <div class="bg-white rounded-xl border border-border shadow-card p-5">
              <div class="flex items-center gap-2 mb-4">
                <div class="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
                  <MapPin class="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <h2 class="text-sm font-semibold">Adresse & contact</h2>
              </div>
              <InfoRow label="Adresse"     value="Non renseigné" muted />
              <InfoRow label="Code postal" :value="displayLead.codePostal" />
              <InfoRow label="Ville"       :value="displayLead.ville" />
              <InfoRow label="Région"      value="Non renseigné" muted />
              <InfoRow label="Pays"        :value="displayLead.pays" />
              <InfoRow label="Email"       :value="displayLead.email" link />
              <InfoRow label="Téléphone"   :value="displayLead.telephone" link />
              <div v-if="displayLead.linkedin_url" class="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                <span class="text-[11px] text-muted-foreground">LinkedIn</span>
                <a :href="displayLead.linkedin_url" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1.5 text-xs font-medium text-tacir-blue hover:underline max-w-[200px] justify-end">
                  <Linkedin class="w-3.5 h-3.5 flex-shrink-0" />
                  <span class="truncate">{{ safeDecode(displayLead.linkedin_url) }}</span>
                </a>
              </div>
              <div v-if="displayLead.website_url" class="flex items-center justify-between py-2 border-b border-border last:border-b-0">
                <span class="text-[11px] text-muted-foreground">Site web</span>
                <a :href="displayLead.website_url" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1.5 text-xs font-medium text-tacir-blue hover:underline max-w-[200px] justify-end">
                  <Globe class="w-3.5 h-3.5 flex-shrink-0" />
                  <span class="truncate">{{ displayLead.website_url }}</span>
                </a>
              </div>
            </div>
          </div>

          <!-- Dirigeants -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center">
                <Users class="w-3.5 h-3.5 text-purple-600" />
              </div>
              <h2 class="text-sm font-semibold">
                Dirigeants & contacts ({{ displayLead.nbDirigeants }})
              </h2>
            </div>
            <p v-if="displayLead.dirigeants.length === 0" class="text-sm text-muted-foreground italic">
              Aucun dirigeant renseigné
            </p>
            <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                v-for="(d, i) in displayLead.dirigeants"
                :key="d.id"
                class="flex items-start gap-3 p-3 rounded-xl bg-muted/40 hover:bg-muted/60 transition-colors"
              >
                <div
                  :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0', AVATAR_COLORS[i % AVATAR_COLORS.length]]"
                >
                  {{ d.initials }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-foreground truncate">{{ d.fullName }}</p>
                  <p class="text-[11px] text-muted-foreground">{{ d.qualite }}</p>
                  <div class="flex items-center gap-3 mt-1.5 flex-wrap">
                    <a
                      v-if="d.email"
                      :href="`mailto:${d.email}`"
                      class="flex items-center gap-1 text-[11px] text-tacir-blue hover:underline"
                    >
                      <Mail class="w-3 h-3" />{{ d.email }}
                    </a>
                    <span v-else class="text-[11px] text-muted-foreground italic">Email non renseigné</span>

                    <a
                      v-if="d.telephone"
                      :href="`tel:${d.telephone}`"
                      class="flex items-center gap-1 text-[11px] text-tacir-blue hover:underline"
                    >
                      <Phone class="w-3 h-3" />{{ d.telephone }}
                    </a>
                    <span v-else class="text-[11px] text-muted-foreground italic">Tél. non renseigné</span>
                  </div>
                </div>
                <div class="flex flex-col items-end gap-1 flex-shrink-0">
                  <div v-if="d.age" class="text-center">
                    <span class="text-base font-semibold text-foreground">{{ d.age }}</span>
                    <span class="text-[10px] text-muted-foreground block">ans</span>
                  </div>
                  <a
                    v-if="d.linkedinUrl"
                    :href="d.linkedinUrl"
                    target="_blank"
                    rel="noreferrer"
                    class="text-blue-600 hover:text-blue-800"
                  >
                    <Linkedin class="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
            <!-- Contact completeness -->
            <div class="flex items-center gap-3 mt-4 pt-4 border-t border-border">
              <span class="text-[11px] text-muted-foreground">Complétude contacts</span>
              <div class="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  class="h-full rounded-full bg-emerald-500 transition-all"
                  :style="{ width: `${contactCompleteness}%` }"
                />
              </div>
              <span class="text-xs font-medium text-emerald-600">{{ contactCompleteness }}%</span>
            </div>
          </div>

          <!-- Indicateurs métier -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center">
                <BarChart3 class="w-3.5 h-3.5 text-amber-600" />
              </div>
              <h2 class="text-sm font-semibold">Indicateurs métier</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard :icon="Target"     label="Score"             :value="`${displayLead.score}/100`" />
              <MetricCard :icon="TrendingUp" label="Proba. conversion" :value="`${displayLead.probaConversion}%`" />
              <MetricCard :icon="Activity"   label="Complétude"        :value="`${displayLead.completude}%`" />
              <MetricCard :icon="Users"      label="Nb dirigeants"     :value="`${displayLead.nbDirigeants}`" />
              <MetricCard :icon="Linkedin"   label="LinkedIn"          :value="displayLead.hasLinkedinDirigeant ? 'Oui' : 'Non'" />
              <MetricCard :icon="Mail"       label="Email"             :value="displayLead.hasEmail ? 'Oui' : 'Non'" />
              <MetricCard :icon="Phone"      label="Téléphone"         :value="displayLead.hasTelephone ? 'Oui' : 'Non'" />
              <MetricCard :icon="Clock"      label="Fraîcheur"         :value="displayLead.dateScrapingFormatted" />
            </div>
          </div>

          <!-- Métadonnées -->
          <div class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-muted flex items-center justify-center">
                <Database class="w-3.5 h-3.5 text-muted-foreground" />
              </div>
              <h2 class="text-sm font-semibold text-muted-foreground">Métadonnées & source</h2>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-x-6">
              <InfoRow label="Date création entreprise" :value="displayLead.dateCreationFormatted" />
              <InfoRow label="Dernière modif. site"     :value="displayLead.dateDerniereModifFormatted" />
              <InfoRow label="Date scraping"            :value="displayLead.dateScrapingFormatted" />
              <InfoRow label="Créé le"                  :value="displayLead.createdAt ? formatDateFR(displayLead.createdAt) : '—'" />
              <InfoRow label="Mis à jour le"            :value="displayLead.updatedAt ? formatDateFR(displayLead.updatedAt) : '—'" />
              <InfoRow label="Raw Lead ID"              :value="displayLead.rawLeadId ?? '—'" />
            </div>
            <!-- ✅ Sources table — refactored -->
            <div v-if="displayLead.sources" class="mt-4 pt-4 border-t border-border">
              <h3 class="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mb-3">Sources de données</h3>
              <div class="overflow-x-auto rounded-xl border border-border shadow-sm">
                <Table>
                  <TableHeader class="bg-muted/50">
                    <TableRow class="hover:bg-transparent">
                      <TableHead 
                        v-for="key in sourceKeys" 
                        :key="key" 
                        class="text-xs font-semibold uppercase text-muted-foreground whitespace-nowrap h-10"
                      >
                        {{ formatSourceKey(key) }}
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow 
                      v-for="(source, idx) in sourcesList" 
                      :key="idx"
                      class="hover:bg-muted/30 transition border-b border-border last:border-0"
                    >
                      <TableCell 
                        v-for="key in sourceKeys" 
                        :key="key"
                        class="text-sm text-foreground py-3 px-4 align-top"
                      >
                        <template v-if="source[key] == null || source[key] === ''">
                          <span class="text-muted-foreground">—</span>
                        </template>
                        <template v-else-if="isUrl(source[key])">
                          <a 
                            :href="source[key]" 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            class="text-primary underline underline-offset-2 hover:opacity-80 truncate max-w-[200px] block"
                            :title="source[key]"
                          >
                            {{ source[key] }}
                          </a>
                        </template>
                        <template v-else>
                          <span class="block max-w-[300px] truncate" :title="String(source[key])">
                            {{ source[key] }}
                          </span>
                        </template>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            </div>
          </div>

          <!-- Appel d'Offre BOAMP -->
          <div v-if="displayLead.infoBoamp" class="bg-white rounded-xl border border-border shadow-card p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-7 h-7 rounded-lg bg-indigo-50 flex items-center justify-center">
                <ClipboardList class="w-3.5 h-3.5 text-indigo-600" />
              </div>
              <h2 class="text-sm font-semibold">📋 Appel d'Offre BOAMP</h2>
            </div>
            
            <div class="space-y-5">
              <!-- Nature -->
              <div v-if="displayLead.infoBoamp.nature" class="flex items-center">
                <span 
                  :class="[
                    'text-xs font-medium px-2.5 py-1 rounded-full border',
                    displayLead.infoBoamp.nature === 'APPEL_OFFRE' 
                      ? 'bg-blue-50 text-tacir-blue border-blue-200' 
                      : 'bg-muted text-muted-foreground border-border'
                  ]"
                >
                  {{ displayLead.infoBoamp.nature }}
                </span>
              </div>

              <!-- Besoin -->
              <div v-if="displayLead.infoBoamp.besoin" class="space-y-1.5">
                <div class="flex items-center gap-2 text-sm font-medium text-foreground">
                  <Lightbulb class="w-4 h-4 text-amber-500" />
                  Besoin identifié
                </div>
                <p class="text-sm text-muted-foreground pl-6 leading-relaxed">
                  {{ displayLead.infoBoamp.besoin }}
                </p>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pl-6">
                <!-- Titulaire -->
                <div v-if="displayLead.infoBoamp.titulaire" class="space-y-1">
                  <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <User class="w-3.5 h-3.5" />
                    Titulaire
                  </div>
                  <p class="text-sm font-medium text-foreground">
                    {{ displayLead.infoBoamp.titulaire }}
                  </p>
                </div>

                <!-- Date limite -->
                <div v-if="displayLead.infoBoamp.date_limite" class="space-y-1">
                  <div class="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Calendar class="w-3.5 h-3.5" />
                    Date limite
                  </div>
                  <p class="text-sm font-medium text-foreground">
                    {{ !isNaN(Date.parse(displayLead.infoBoamp.date_limite)) ? new Date(displayLead.infoBoamp.date_limite).toLocaleDateString('fr-FR') : displayLead.infoBoamp.date_limite }}
                  </p>
                </div>
              </div>

              <!-- Infos complémentaires -->
              <div v-if="displayLead.infoBoamp.info_complementaire" class="space-y-1.5">
                <div class="flex items-center gap-2 text-sm font-medium text-foreground">
                  <Info class="w-4 h-4 text-blue-500" />
                  Infos complémentaires
                </div>
                <p class="text-sm text-muted-foreground pl-6 leading-relaxed whitespace-pre-wrap">
                  {{ displayLead.infoBoamp.info_complementaire }}
                </p>
              </div>

              <!-- Lien de l'offre -->
              <div v-if="displayLead.infoBoamp.lienOffre" class="pt-2">
                <a 
                  :href="displayLead.infoBoamp.lienOffre" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  class="inline-flex items-center gap-2 h-9 px-4 text-sm font-medium rounded-md border border-input bg-white hover:bg-accent hover:text-accent-foreground transition-colors"
                >
                  Voir l'offre BOAMP
                  <ExternalLink class="w-4 h-4" />
                </a>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pb-8">
            <button class="inline-flex items-center gap-2 h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors">
              <RefreshCw class="w-3.5 h-3.5" /> Prospects similaires
            </button>
            <Button 
              v-if="displayLead.infoBoamp"
              @click="generateEmail"
              :disabled="isGeneratingEmail"
              class="gap-2 bg-blue-600 text-white hover:bg-blue-700 h-9"
            >
              <Loader2 v-if="isGeneratingEmail" class="w-4 h-4 animate-spin" />
              <Mail v-else class="w-4 h-4" />
              {{ isGeneratingEmail ? 'Génération en cours...' : '✉ Générer un email' }}
            </Button>
            <Button 
              v-else
              @click="showAnalysis = true"
              class="gap-2 bg-tacir-blue text-white hover:opacity-90 h-9"
            >
              <Sparkles class="w-4 h-4" />
              Analyser le potentiel
            </Button>
          </div>

  <LinkedInAnalysisFlow 
    v-if="showAnalysis"
    :is-open="showAnalysis"
    :company-name="displayLead.nom" 
    :company-id="displayLead.id"
    :lead="displayLead"
    @update:is-open="showAnalysis = $event"
    @analysis-complete="onAnalysisComplete"
  />

        </div>
      </main>
    </div>
  </div>

  <!-- Email Modal -->
  <Dialog :open="showEmailModal" @update:open="showEmailModal = $event">
    <DialogContent class="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
      <DialogHeader class="px-6 py-4 border-b">
        <DialogTitle class="flex items-center gap-2">
          <Mail class="w-5 h-5 text-primary" /> Email de prospection généré
        </DialogTitle>
        <DialogDescription>
          Vous pouvez ajuster le contenu avant de le copier.
        </DialogDescription>
      </DialogHeader>
      
      <div class="space-y-4 px-6 py-4 flex-1 overflow-y-auto">
        <div class="space-y-2">
          <Label for="email-subject">Objet</Label>
          <Input id="email-subject" v-model="generatedEmailSubject" />
        </div>
        <div class="space-y-2">
          <Label for="email-body">Corps de l'email</Label>
          <Textarea 
            id="email-body"
            v-model="generatedEmailBody" 
            class="min-h-[300px] resize-y"
          />
        </div>
      </div>

      <DialogFooter class="flex sm:justify-between items-center gap-3 px-6 py-4 border-t bg-muted/20">
        <p v-if="emailError" class="text-sm text-red-500">{{ emailError }}</p>
        <div class="flex gap-2 w-full sm:w-auto justify-end ml-auto">
          <Button variant="outline" @click="showEmailModal = false">
            Fermer
          </Button>
          <Button @click="copyGeneratedEmail" class="gap-2">
            <Check v-if="emailCopied" class="w-4 h-4" />
            <Copy v-else class="w-4 h-4" />
            {{ emailCopied ? 'Copié !' : 'Copier' }}
          </Button>
        </div>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- Edit modal -->
  <LeadEditModal
    v-if="displayLead"
    :lead="editOpen ? displayLead : null"
    :open="editOpen"
    @close="editOpen = false"
    @save="handleSave"
  />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowLeft, Pencil, Trash2, MapPin, Phone, Mail, Linkedin,
  Users, FileText, BarChart3, Target, TrendingUp, Activity,
  Clock, Database, RefreshCw, Loader2, Sparkles, Globe,
  ClipboardList, Lightbulb, ExternalLink, User, Calendar, Info,
  Check, Copy
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Button } from '@/components/ui/button'
import Textarea from '@/components/ui/textarea/Textarea.vue'
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter 
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell
} from '@/components/ui/table'

import TheSidebar    from '@/components/AppSidebar.vue'
import SegmentBadge  from '@/components/leads/SegmentBadge.vue'
import StatusBadge   from '@/components/leads/StatusBadge.vue'
import ScoreRing     from '@/components/leads/ScoreRing.vue'
import InfoRow       from '@/components/leads/InfoRow.vue'
import MetricCard    from '@/components/leads/MetricCard.vue'
import LeadEditModal from '@/components/leads/LeadEditModal.vue'
import LinkedInAnalysisFlow from '@/components/leads/LinkedInAnalysisFlow.vue'

import axios from 'axios'
import { adaptLead, formatDateFR } from '@/lib/leadAdapter'

const route  = useRoute()
const router = useRouter()

const leadFromApi = ref(null)
const isLoading = ref(true)

// Local overrides for optimistic edits
const localLead  = ref(null)
const displayLead = computed(() => localLead.value ?? leadFromApi.value)

const editOpen = ref(false)

const sourcesList = computed(() => {
  if (!displayLead.value || !displayLead.value.sources) return []
  return Array.isArray(displayLead.value.sources) ? displayLead.value.sources : [displayLead.value.sources]
})

const sourceKeys = computed(() => {
  if (sourcesList.value.length === 0) return []
  const keys = new Set()
  sourcesList.value.forEach(s => {
    if (s && typeof s === 'object') {
      Object.keys(s).forEach(k => keys.add(k))
    }
  })
  return Array.from(keys)
})

function formatSourceKey(key) {
  const map = {
    nom: 'Source',
    ville: 'Ville',
    date_publication: 'Date de publication',
    url: 'Lien',
    source: 'Source',
  }
  if (map[key]) return map[key]
  return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

function isUrl(str) {
  if (typeof str !== 'string') return false
  return str.startsWith('http://') || str.startsWith('https://')
}

const safeDecode = (url) => {
  try {
    return decodeURIComponent(url)
  } catch (e) {
    return url
  }
}

async function fetchLeadDetails() {
  isLoading.value = true
  try {
    const baseUrl = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
    const res = await axios.get(`${baseUrl}/entreprises/${route.params.id}`)
    leadFromApi.value = adaptLead(res.data, 0)
  } catch (err) {
    console.error('[LeadDetail] Fetch error:', err)
  } finally {
    isLoading.value = false
  }
}


onMounted(() => {
  fetchLeadDetails()
})

// ---- Computed ----
const initials = computed(() => {
  if (!displayLead.value) return ''
  return displayLead.value.nom
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0] ?? '')
    .join('')
    .toUpperCase()
})

const contactCompleteness = computed(() => {
  if (!displayLead.value || displayLead.value.nbDirigeants === 0) return 0
  const dirs = displayLead.value.dirigeants
  // 3 contact fields per dirigeant: email, telephone, LinkedIn
  const totalFields = dirs.length * 3
  const filledFields = dirs.reduce((sum, d) => {
    return sum
      + (d.email      ? 1 : 0)
      + (d.telephone  ? 1 : 0)
      + (d.linkedinUrl ? 1 : 0)
  }, 0)
  return Math.round((filledFields / totalFields) * 100)
})

// ---- Constants ----
const AVATAR_COLORS = [
  'bg-purple-50 text-purple-700',
  'bg-emerald-50 text-emerald-700',
  'bg-orange-50 text-orange-700',
  'bg-blue-50 text-blue-700',
  'bg-rose-50 text-rose-700',
]

// ---- Analysis Handlers ----
const showAnalysis = ref(false)

const onAnalysisComplete = (data) => {
  showAnalysis.value = false
  // TODO: send data to backend or update local lead implicitly
  console.log('Analysis result:', data)
}

function onAnalysisSkip() {
  console.log('Analyse ignorée')
  showAnalysis.value = false
}

// ---- Email Generation Handlers ----
const isGeneratingEmail = ref(false)
const showEmailModal = ref(false)
const generatedEmailSubject = ref('')
const generatedEmailBody = ref('')
const emailCopied = ref(false)
const emailError = ref('')

const generateEmail = async () => {
  if (!displayLead.value || !displayLead.value.infoBoamp) return;
  
  isGeneratingEmail.value = true
  emailError.value = ''
  
  try {
    const payload = {
      rapport: {
        nom_entreprise: displayLead.value.nom,
        besoin: displayLead.value.infoBoamp.besoin
      },
      remarques: ''
    }
    
    const baseUrl = import.meta.env.VITE_IA_SERVICE_URL || 'http://localhost:8002'
    const response = await axios.post(`${baseUrl}/ia/generate-email`, payload)
    
    generatedEmailSubject.value = response.data.objet || 'Proposition de collaboration Numeryx'
    generatedEmailBody.value = response.data.corps || ''
    
    showEmailModal.value = true
  } catch (err) {
    console.error('Error generating email:', err)
    emailError.value = err.response?.data?.detail || "Erreur lors de la génération de l'email."
    toast.error(emailError.value)
  } finally {
    isGeneratingEmail.value = false
  }
}

const copyGeneratedEmail = async () => {
  const fullEmail = `Objet : ${generatedEmailSubject.value}\n\n${generatedEmailBody.value}`
  try {
    await navigator.clipboard.writeText(fullEmail)
    emailCopied.value = true
    setTimeout(() => { emailCopied.value = false }, 2000)
    toast.success("Email copié dans le presse-papiers !")
  } catch (err) {
    console.error('Failed to copy', err)
    toast.error("Erreur lors de la copie")
  }
}

// ---- Handlers ----
function handleSave(id, updates) {
  localLead.value = { ...(displayLead.value ?? {}), ...updates }
  editOpen.value = false
}
</script>

<style scoped>
.shadow-card {
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(48,62,140,0.06);
}
</style>
