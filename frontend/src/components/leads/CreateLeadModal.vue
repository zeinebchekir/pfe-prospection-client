<template>
  <Dialog :open="open" @update:open="handleOpenChange">
    <DialogContent class="w-[calc(100vw-2rem)] sm:max-w-2xl max-h-[92vh] p-0 flex flex-col overflow-hidden">

      <!-- ── HEADER ─────────────────────────────────────────────── -->
      <DialogHeader class="px-6 pt-6 pb-4 flex-shrink-0 border-b border-border">
        <DialogTitle class="text-base font-semibold flex items-center gap-2">
          <span class="w-8 h-8 rounded-xl bg-tacir-blue/10 flex items-center justify-center flex-shrink-0">
            <PlusCircle class="w-4 h-4 text-tacir-blue" />
          </span>
          Créer un nouveau lead
        </DialogTitle>
        <p class="text-[11px] text-muted-foreground mt-1.5 leading-relaxed">
          Seul le <strong class="text-foreground">nom</strong> est obligatoire.
          Les autres champs sont optionnels mais validés dès que vous les remplissez.
        </p>
      </DialogHeader>

      <!-- ── TABS NAV ───────────────────────────────────────────── -->
      <div class="px-6 pt-3 flex-shrink-0">
        <div class="flex border-b border-border gap-0.5">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            :class="[
              'relative px-4 py-2 text-xs font-medium border-b-2 -mb-px transition-all',
              activeTab === tab.key
                ? 'border-tacir-blue text-tacir-blue'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
            ]"
          >
            {{ tab.label }}
            <!-- Red dot: tab has validation errors -->
            <span
              v-if="tabHasError(tab.key)"
              class="absolute -top-0.5 right-0.5 w-2 h-2 rounded-full bg-red-500 ring-2 ring-white"
            />
            <!-- Count badge for dirigeants -->
            <span
              v-else-if="tab.key === 'dirigeants' && formDirigeants.length"
              class="ml-1.5 text-[9px] font-bold bg-tacir-blue/10 text-tacir-blue px-1.5 py-0.5 rounded-full"
            >
              {{ formDirigeants.length }}
            </span>
          </button>
        </div>
      </div>

      <!-- ── TAB CONTENT ────────────────────────────────────────── -->
      <div class="flex-1 overflow-y-auto px-6 py-5">

        <!-- API error banner -->
        <Transition name="fade-err">
          <div
            v-if="apiError"
            class="mb-5 flex items-start gap-3 px-4 py-3 rounded-xl border border-red-200 bg-red-50 text-red-700"
          >
            <AlertCircle class="w-4 h-4 flex-shrink-0 mt-0.5" />
            <p class="text-xs font-medium leading-relaxed flex-1">{{ apiError }}</p>
            <button @click="apiError = ''" class="text-red-400 hover:text-red-600">
              <X class="w-3.5 h-3.5" />
            </button>
          </div>
        </Transition>

        <!-- ═══════════════════════════════════════════════ -->
        <!--  TAB 1 — INFORMATIONS                          -->
        <!-- ═══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'general'" class="space-y-5">

          <!-- Nom -->
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-foreground">
              Nom de l'entreprise
              <span class="text-red-500 ml-0.5">*</span>
            </label>
            <input
              v-model="form.nom"
              type="text"
              placeholder="Ex : ACME Corp, Sofrecom…"
              :class="iClass('nom')"
              @blur="touch('nom')"
            />
            <p v-if="showErr('nom')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
              <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.nom }}
            </p>
          </div>

          <!-- SIREN + SIRET -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">SIREN</label>
              <p class="text-[10px] text-muted-foreground -mt-0.5">Identifiant national à 9 chiffres</p>
              <input
                v-model="form.siren"
                type="text"
                placeholder="Ex : 123456789"
                maxlength="9"
                :class="iClass('siren')"
                @blur="touch('siren')"
                @input="form.siren = form.siren.replace(/\D/g, '').slice(0, 9)"
              />
              <p v-if="showErr('siren')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.siren }}
              </p>
              <!-- Progress ring: digits entered -->
              <div v-if="form.siren && !errors.siren" class="flex items-center gap-1.5 mt-1">
                <div class="flex gap-px">
                  <span
                    v-for="n in 9" :key="n"
                    :class="['w-1.5 h-1.5 rounded-full', n <= form.siren.length ? 'bg-tacir-lightblue' : 'bg-border']"
                  />
                </div>
                <span class="text-[9px] text-muted-foreground">{{ form.siren.length }}/9</span>
              </div>
            </div>

            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">SIRET</label>
              <p class="text-[10px] text-muted-foreground -mt-0.5">Identifiant établissement à 14 chiffres</p>
              <input
                v-model="form.siret"
                type="text"
                placeholder="Ex : 12345678900001"
                maxlength="14"
                :class="iClass('siret')"
                @blur="touch('siret')"
                @input="form.siret = form.siret.replace(/\D/g, '').slice(0, 14)"
              />
              <p v-if="showErr('siret')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.siret }}
              </p>
              <div v-if="form.siret && !errors.siret" class="flex items-center gap-1.5 mt-1">
                <div class="flex gap-px">
                  <span
                    v-for="n in 14" :key="n"
                    :class="['w-1 h-1.5 rounded-full', n <= form.siret.length ? 'bg-tacir-lightblue' : 'bg-border']"
                  />
                </div>
                <span class="text-[9px] text-muted-foreground">{{ form.siret.length }}/14</span>
              </div>
            </div>
          </div>

          <!-- Secteur + Forme juridique -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Secteur d'activité</label>
              <input
                v-model="form.secteur_activite"
                type="text"
                placeholder="Ex : Programmation informatique"
                :class="iClass()"
              />
            </div>
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Forme juridique</label>
              <input
                v-model="form.forme_juridique"
                type="text"
                placeholder="Ex : SAS, SARL, SA…"
                :class="iClass()"
              />
            </div>
          </div>

          <!-- Taille + CA -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Taille entreprise</label>
              <input
                v-model="form.taille_entreprise"
                type="text"
                placeholder="Ex : 10-19 salariés"
                :class="iClass()"
              />
            </div>
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">
                Chiffre d'affaires
                <span class="text-muted-foreground font-normal ml-1">(€)</span>
              </label>
              <input
                v-model="form.ca"
                type="number"
                min="0"
                step="1000"
                placeholder="Ex : 1500000"
                :class="iClass('ca')"
                @blur="touch('ca')"
              />
              <p v-if="showErr('ca')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.ca }}
              </p>
              <!-- Formatted preview -->
              <p v-else-if="form.ca && !errors.ca" class="text-[10px] text-tacir-lightblue font-medium mt-1">
                ≈ {{ formatCAPreview(form.ca) }}
              </p>
            </div>
          </div>

          <!-- Date création + Nb locaux -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Date de création</label>
              <input
                v-model="form.date_creation"
                type="date"
                :max="todayISO"
                :class="iClass('date_creation')"
                @blur="touch('date_creation')"
              />
              <p v-if="showErr('date_creation')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.date_creation }}
              </p>
            </div>
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Nombre de locaux</label>
              <input
                v-model="form.nb_locaux"
                type="number"
                min="0"
                step="1"
                placeholder="Ex : 2"
                :class="iClass('nb_locaux')"
                @blur="touch('nb_locaux')"
              />
              <p v-if="showErr('nb_locaux')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.nb_locaux }}
              </p>
            </div>
          </div>

          <!-- Statut -->
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-foreground">Statut commercial</label>
            <div class="flex gap-2 flex-wrap">
              <button
                v-for="s in STATUTS"
                :key="s.value"
                @click="form.statut = s.value"
                :class="[
                  'h-8 px-3 rounded-lg text-xs font-medium border transition-all',
                  form.statut === s.value
                    ? s.active
                    : 'border-border text-muted-foreground hover:border-tacir-blue/30 hover:text-tacir-blue'
                ]"
              >
                {{ s.label }}
              </button>
            </div>
          </div>

        </div>

        <!-- ═══════════════════════════════════════════════ -->
        <!--  TAB 2 — CONTACT                               -->
        <!-- ═══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'contact'" class="space-y-5">

          <!-- Ville + Code postal -->
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Ville</label>
              <input
                v-model="form.ville"
                type="text"
                placeholder="Ex : Paris"
                :class="iClass()"
              />
            </div>
            <div class="space-y-1.5">
              <label class="block text-xs font-semibold text-foreground">Code postal</label>
              <p class="text-[10px] text-muted-foreground -mt-0.5">5 chiffres pour la France</p>
              <input
                v-model="form.code_postal"
                type="text"
                placeholder="Ex : 75001"
                maxlength="5"
                :class="iClass('code_postal')"
                @blur="touch('code_postal')"
                @input="form.code_postal = form.code_postal.replace(/\D/g, '').slice(0, 5)"
              />
              <p v-if="showErr('code_postal')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
                <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.code_postal }}
              </p>
            </div>
          </div>

          <!-- Pays -->
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-foreground">Pays</label>
            <input
              v-model="form.pays"
              type="text"
              placeholder="France"
              :class="iClass()"
            />
          </div>

          <!-- Téléphone -->
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-foreground">
              Téléphone
            </label>
            <p class="text-[10px] text-muted-foreground -mt-0.5">
              Format international recommandé : +33 1 23 45 67 89
            </p>
            <div class="relative">
              <Phone class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                v-model="form.telephone"
                type="tel"
                placeholder="+33 1 23 45 67 89"
                :class="[iClass('telephone'), 'pl-9']"
                @blur="touch('telephone')"
              />
            </div>
            <p v-if="showErr('telephone')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
              <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.telephone }}
            </p>
          </div>

          <!-- Email -->
          <div class="space-y-1.5">
            <label class="block text-xs font-semibold text-foreground">Email</label>
            <p class="text-[10px] text-muted-foreground -mt-0.5">Adresse email de contact de l'entreprise</p>
            <div class="relative">
              <Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
              <input
                v-model="form.email"
                type="text"
                placeholder="contact@entreprise.fr"
                :class="[iClass('email'), 'pl-9']"
                @blur="touch('email')"
              />
            </div>
            <p v-if="showErr('email')" class="flex items-center gap-1.5 text-[11px] text-red-600 font-medium mt-1">
              <AlertCircle class="w-3 h-3 flex-shrink-0" />{{ errors.email }}
            </p>
            <!-- Valid check -->
            <p v-else-if="form.email && !errors.email" class="flex items-center gap-1.5 text-[11px] text-emerald-600 font-medium mt-1">
              <CheckCircle2 class="w-3 h-3 flex-shrink-0" /> Email valide
            </p>
          </div>
        </div>

        <!-- ═══════════════════════════════════════════════ -->
        <!--  TAB 3 — DIRIGEANTS                            -->
        <!-- ═══════════════════════════════════════════════ -->
        <div v-if="activeTab === 'dirigeants'" class="space-y-4">

          <!-- Header -->
          <div class="flex items-center justify-between pb-2 border-b border-border">
            <div>
              <p class="text-xs font-semibold text-foreground flex items-center gap-1.5">
                <Users class="w-3.5 h-3.5 text-tacir-blue" />
                Dirigeants de l'entreprise
              </p>
              <p class="text-[10px] text-muted-foreground mt-0.5">
                Ajoutez les dirigeants connus (nom requis pour chaque entrée)
              </p>
            </div>
            <button
              @click="addDirigeant"
              class="inline-flex items-center gap-1.5 h-8 px-3 text-xs font-semibold rounded-lg bg-tacir-blue text-white hover:opacity-90 transition-all active:scale-95 shadow-sm"
            >
              <Plus class="w-3.5 h-3.5" /> Ajouter un dirigeant
            </button>
          </div>

          <!-- Empty state -->
          <div
            v-if="formDirigeants.length === 0"
            class="flex flex-col items-center justify-center py-10 rounded-xl border-2 border-dashed border-border text-center"
          >
            <div class="w-10 h-10 rounded-full bg-muted flex items-center justify-center mb-3">
              <Users class="w-5 h-5 text-muted-foreground" />
            </div>
            <p class="text-sm font-medium text-muted-foreground">Aucun dirigeant ajouté</p>
            <p class="text-[11px] text-muted-foreground/70 mt-1">Cliquez sur "Ajouter un dirigeant" pour commencer</p>
          </div>

          <!-- Dirigeant cards -->
          <div class="space-y-4">
            <div
              v-for="(d, i) in formDirigeants"
              :key="d._uid"
              class="rounded-xl border bg-card transition-all"
              :class="hasBlankDirigeantNom(i) && submitted
                ? 'border-red-300 shadow-sm shadow-red-100'
                : 'border-border hover:border-tacir-blue/25'"
            >
              <!-- Card header -->
              <div class="flex items-center justify-between px-4 py-3 border-b border-border/60">
                <div class="flex items-center gap-2.5">
                  <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-[11px] font-bold flex-shrink-0', AVATAR_COLORS[i % AVATAR_COLORS.length]]">
                    {{ getInitials(d.prenom, d.nom) }}
                  </div>
                  <div>
                    <p class="text-xs font-semibold text-foreground">
                      {{ [d.prenom, d.nom].filter(Boolean).join(' ') || 'Nouveau dirigeant' }}
                    </p>
                    <p class="text-[10px] text-muted-foreground">{{ d.role || 'Rôle non défini' }}</p>
                  </div>
                </div>
                <button
                  @click="removeDirigeant(i)"
                  class="h-7 w-7 flex items-center justify-center rounded-md hover:bg-red-50 hover:text-red-600 text-muted-foreground transition-colors"
                  title="Supprimer ce dirigeant"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>

              <!-- Card fields -->
              <div class="p-4 grid grid-cols-2 gap-3">

                <!-- Prénom -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">Prénom</label>
                  <input
                    v-model="d.prenom"
                    type="text"
                    placeholder="Jean"
                    class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue transition-colors"
                  />
                </div>

                <!-- Nom (required) -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                    Nom <span class="text-red-500 normal-case font-bold">*</span>
                  </label>
                  <input
                    v-model="d.nom"
                    type="text"
                    placeholder="DUPONT"
                    :class="[
                      'w-full h-8 text-sm rounded-md border bg-background px-2.5 focus:outline-none focus:ring-1 transition-colors',
                      hasBlankDirigeantNom(i) && submitted
                        ? 'border-red-400 focus:ring-red-300 bg-red-50/30'
                        : 'border-input focus:ring-tacir-blue'
                    ]"
                  />
                  <p v-if="hasBlankDirigeantNom(i) && submitted" class="flex items-center gap-1 text-[10px] text-red-600 font-medium">
                    <AlertCircle class="w-2.5 h-2.5" /> Nom requis
                  </p>
                </div>

                <!-- Rôle -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">Rôle / Qualité</label>
                  <input
                    v-model="d.role"
                    type="text"
                    placeholder="Ex : Gérant, Président…"
                    class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue transition-colors"
                  />
                </div>

                <!-- Nationalité -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">Nationalité</label>
                  <input
                    v-model="d.nationalite"
                    type="text"
                    placeholder="Ex : Française"
                    class="w-full h-8 text-sm rounded-md border border-input bg-background px-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue transition-colors"
                  />
                </div>

                <!-- Email dirigeant -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                    <Mail class="w-3 h-3" /> Email
                  </label>
                  <div class="relative">
                    <Mail class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
                    <input
                      v-model="d.email"
                      type="email"
                      placeholder="jean.dupont@entreprise.fr"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background pl-7 pr-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue transition-colors"
                    />
                  </div>
                </div>

                <!-- Téléphone dirigeant -->
                <div class="space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                    <Phone class="w-3 h-3" /> Téléphone
                  </label>
                  <div class="relative">
                    <Phone class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-muted-foreground" />
                    <input
                      v-model="d.telephone"
                      type="tel"
                      placeholder="+33 6 12 34 56 78"
                      class="w-full h-8 text-sm rounded-md border border-input bg-background pl-7 pr-2.5 focus:outline-none focus:ring-1 focus:ring-tacir-blue transition-colors"
                    />
                  </div>
                </div>

                <!-- LinkedIn URL (full width) -->
                <div class="col-span-2 space-y-1">
                  <label class="block text-[10px] font-semibold text-muted-foreground uppercase tracking-wide flex items-center gap-1">
                    <Linkedin class="w-3 h-3 text-[#0A66C2]" />
                    Profil LinkedIn
                  </label>
                  <div class="relative">
                    <Linkedin class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-[#0A66C2]" />
                    <input
                      v-model="d.linkedin_url"
                      type="url"
                      placeholder="https://linkedin.com/in/jean-dupont"
                      :class="[
                        'w-full h-8 text-sm rounded-md border bg-background pl-7 pr-2.5 focus:outline-none focus:ring-1 transition-colors',
                        d.linkedin_url && !isValidUrl(d.linkedin_url)
                          ? 'border-amber-400 focus:ring-amber-300'
                          : 'border-input focus:ring-tacir-blue'
                      ]"
                    />
                  </div>
                  <p v-if="d.linkedin_url && !isValidUrl(d.linkedin_url)" class="flex items-center gap-1 text-[10px] text-amber-600 font-medium">
                    <AlertCircle class="w-2.5 h-2.5" /> URL invalide — commencez par https://
                  </p>
                  <p v-else-if="d.linkedin_url && isValidUrl(d.linkedin_url)" class="flex items-center gap-1 text-[10px] text-emerald-600 font-medium">
                    <CheckCircle2 class="w-2.5 h-2.5" /> URL valide
                  </p>
                </div>

              </div>
            </div>
          </div>
        </div>

      </div>

      <!-- ── FOOTER ──────────────────────────────────────────────── -->
      <div class="flex-shrink-0 border-t border-border px-4 sm:px-6 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-muted/20">
        <!-- Error summary -->
        <div>
          <p v-if="submitted && totalErrors > 0" class="flex items-center gap-1.5 text-xs text-red-600 font-semibold">
            <AlertCircle class="w-3.5 h-3.5" />
            {{ totalErrors }} erreur{{ totalErrors !== 1 ? 's' : '' }} à corriger
          </p>
          <p v-else-if="submitted && totalErrors === 0" class="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
            <CheckCircle2 class="w-3.5 h-3.5" /> Tous les champs sont valides
          </p>
        </div>

        <div class="flex items-center gap-3 w-full sm:w-auto">
          <button
            @click="handleClose"
            :disabled="isSaving"
            class="flex-1 sm:flex-none h-9 px-4 text-sm rounded-md border border-input hover:bg-accent transition-colors disabled:opacity-50"
          >
            Annuler
          </button>
          <button
            @click="handleCreate"
            :disabled="isSaving"
            class="flex-1 sm:flex-none h-9 px-5 text-sm font-semibold rounded-md bg-tacir-blue text-white hover:opacity-90 active:scale-95 transition-all flex items-center justify-center gap-2 disabled:opacity-60 shadow-sm"
          >
            <Loader2 v-if="isSaving" class="h-4 w-4 animate-spin" />
            <PlusCircle v-else class="h-4 w-4" />
            {{ isSaving ? 'Création en cours…' : 'Créer le lead' }}
          </button>
        </div>
      </div>

    </DialogContent>
  </Dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import {
  Users, Loader2, Plus, Trash2, PlusCircle, AlertCircle, X,
  Phone, Mail, CheckCircle2, Linkedin,
} from 'lucide-vue-next'
import { toast } from 'vue-sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { adaptLead } from '@/lib/leadAdapter'

// ── Props / Emits ────────────────────────────────────────────────
const props = defineProps({ open: { type: Boolean, default: false } })
const emit  = defineEmits(['close', 'created'])

// ── Constants ────────────────────────────────────────────────────
const BASE_URL = import.meta.env.VITE_FASTAPI_URL || 'http://localhost:8001'
const todayISO = new Date().toISOString().split('T')[0]

const tabs = [
  { key: 'general',    label: 'Informations' },
  { key: 'contact',    label: 'Contact'      },
  { key: 'dirigeants', label: 'Dirigeants'   },
]

const STATUTS = [
  { value: 'Nouveau',     label: 'Nouveau',     active: 'border-tacir-blue bg-tacir-blue/10 text-tacir-blue' },
  { value: 'Qualifié',   label: 'Qualifié',    active: 'border-emerald-500 bg-emerald-50 text-emerald-700' },
  { value: 'Opportunité', label: 'Opportunité', active: 'border-amber-500 bg-amber-50 text-amber-700' },
]

const AVATAR_COLORS = [
  'bg-purple-100 text-purple-700', 'bg-emerald-100 text-emerald-700',
  'bg-orange-100 text-orange-700', 'bg-blue-100 text-blue-700',
  'bg-rose-100 text-rose-700',     'bg-teal-100 text-teal-700',
]

const GENERAL_FIELDS = ['nom', 'siren', 'siret', 'ca', 'nb_locaux', 'date_creation']
const CONTACT_FIELDS = ['email', 'telephone', 'code_postal']

// ── State ────────────────────────────────────────────────────────
const activeTab = ref('general')
const isSaving  = ref(false)
const submitted = ref(false)
const touched   = ref(new Set())
const apiError  = ref('')

const emptyForm = () => ({
  nom: '', siren: '', siret: '',
  secteur_activite: '', forme_juridique: '', taille_entreprise: '',
  date_creation: '', ca: '', nb_locaux: '',
  statut: 'Nouveau',
  ville: '', code_postal: '', pays: 'France',
  telephone: '', email: '',
})

const form           = ref(emptyForm())
const formDirigeants = ref([])

// ── Regex helpers ────────────────────────────────────────────────
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const PHONE_RE = /^[+\d][\d\s\-.()+]{6,19}$/

function isValidUrl(url) {
  try { new URL(url); return true } catch { return false }
}

// ── Validation (reactive computed) ───────────────────────────────
const errors = computed(() => {
  const f   = form.value
  const err = {}

  if (!f.nom.trim())
    err.nom = 'Le nom de l\'entreprise est obligatoire.'

  if (f.siren && !/^\d{9}$/.test(f.siren))
    err.siren = `SIREN invalide : ${f.siren.length}/9 chiffres saisie${f.siren.length > 9 ? 's' : ''}.`

  if (f.siret && !/^\d{14}$/.test(f.siret))
    err.siret = `SIRET invalide : ${f.siret.length}/14 chiffres saisis.`

  if (f.siren && f.siret && f.siret.length === 14 && !f.siret.startsWith(f.siren))
    err.siret = err.siret || 'Le SIRET doit commencer par le SIREN renseigné.'

  if (f.ca !== '' && f.ca !== null) {
    const n = parseFloat(f.ca)
    if (isNaN(n) || n < 0)
      err.ca = 'Le chiffre d\'affaires doit être un nombre positif ou nul.'
  }

  if (f.nb_locaux !== '' && f.nb_locaux !== null) {
    const n = Number(f.nb_locaux)
    if (!Number.isInteger(n) || n < 0)
      err.nb_locaux = 'Le nombre de locaux doit être un entier positif ou nul.'
  }

  if (f.date_creation && f.date_creation > todayISO)
    err.date_creation = 'La date de création ne peut pas être dans le futur.'

  if (f.email && !EMAIL_RE.test(f.email.trim()))
    err.email = 'Adresse email invalide — ex: contact@entreprise.fr'

  if (f.telephone && !PHONE_RE.test(f.telephone.trim()))
    err.telephone = 'Numéro de téléphone invalide — ex: +33 1 23 45 67 89'

  if (f.code_postal && !/^\d{5}$/.test(f.code_postal))
    err.code_postal = 'Le code postal doit contenir exactement 5 chiffres.'

  return err
})

// ── Show error: only after touch or submit ───────────────────────
function showErr(field) {
  return (submitted.value || touched.value.has(field)) && !!errors.value[field]
}

function touch(field) {
  touched.value = new Set([...touched.value, field])
}

// ── Field input CSS class ────────────────────────────────────────
function iClass(field) {
  const base = 'w-full h-9 text-sm rounded-md border bg-background px-3 focus:outline-none focus:ring-2 transition-colors'
  if (field && showErr(field))
    return `${base} border-red-400 focus:ring-red-200 bg-red-50/30`
  return `${base} border-input focus:ring-ring`
}

// ── Tab error dot logic ──────────────────────────────────────────
function tabHasError(key) {
  if (!submitted.value) return false
  const e = errors.value
  if (key === 'general')    return GENERAL_FIELDS.some(f => e[f])
  if (key === 'contact')    return CONTACT_FIELDS.some(f => e[f])
  if (key === 'dirigeants') return formDirigeants.value.some(d => !d.nom?.trim())
  return false
}

const totalErrors = computed(() => {
  return Object.keys(errors.value).length +
         formDirigeants.value.filter(d => !d.nom?.trim()).length
})

// ── CA formatted preview ─────────────────────────────────────────
function formatCAPreview(ca) {
  const n = parseFloat(ca)
  if (isNaN(n)) return ''
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2).replace('.', ',')} M€`
  if (n >= 1_000)     return `${(n / 1_000).toFixed(0)} k€`
  return `${n} €`
}

// ── Dirigeant helpers ─────────────────────────────────────────────
let _uid = 0
const nextUid = () => ++_uid

function getInitials(prenom, nom) {
  return ((prenom?.[0] ?? '') + (nom?.[0] ?? '')).toUpperCase() || '?'
}

function addDirigeant() {
  formDirigeants.value.push({
    _uid: nextUid(),
    prenom: '', nom: '', role: '',
    nationalite: '', linkedin_url: '',
    email: '', telephone: '',
  })
}

function removeDirigeant(i) { formDirigeants.value.splice(i, 1) }

function hasBlankDirigeantNom(i) {
  return !formDirigeants.value[i]?.nom?.trim()
}

// ── Reset ────────────────────────────────────────────────────────
function resetState() {
  form.value           = emptyForm()
  formDirigeants.value = []
  activeTab.value      = 'general'
  submitted.value      = false
  touched.value        = new Set()
  apiError.value       = ''
  isSaving.value       = false
}

function handleClose() {
  if (isSaving.value) return
  resetState()
  emit('close')
}

function handleOpenChange(val) {
  if (!val) handleClose()
}

// ── Payload builder ───────────────────────────────────────────────
function buildPayload() {
  const f    = form.value
  const trim = (v) => (v === '' || v == null) ? undefined : String(v).trim() || undefined

  return {
    nom:                      f.nom.trim(),
    siren:                    trim(f.siren),
    siret:                    trim(f.siret),
    ville:                    trim(f.ville),
    code_postal:              trim(f.code_postal),
    pays:                     trim(f.pays) || 'France',
    secteur_activite:         trim(f.secteur_activite),
    forme_juridique:          trim(f.forme_juridique),
    taille_entreprise:        trim(f.taille_entreprise),
    nb_locaux:                f.nb_locaux !== '' ? Number(f.nb_locaux) : undefined,
    ca:                       f.ca        !== '' ? parseFloat(f.ca)   : undefined,
    date_creation_entreprise: trim(f.date_creation),
    telephone:                trim(f.telephone),
    email:                    trim(f.email),
    statut:                   f.statut || 'Nouveau',
    dirigeants:               formDirigeants.value.length
      ? formDirigeants.value.map(({ _uid: _, ...d }) => d)
      : undefined,
  }
}

// ── API error extractor ───────────────────────────────────────────
function extractError(err) {
  const data = err?.response?.data
  if (!data) return 'Une erreur inattendue s\'est produite. Veuillez réessayer.'
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail) && data.detail.length > 0)
    return data.detail[0]?.msg || 'Données invalides.'
  return data.message || 'Une erreur inattendue s\'est produite.'
}

// ── Submit ────────────────────────────────────────────────────────
async function handleCreate() {
  submitted.value = true
  apiError.value  = ''

  const hasFormErrors = Object.keys(errors.value).length > 0
  const hasDirErrors  = formDirigeants.value.some(d => !d.nom?.trim())

  if (hasFormErrors || hasDirErrors) {
    // Jump to first tab with errors
    if (GENERAL_FIELDS.some(f => errors.value[f]))      { activeTab.value = 'general' }
    else if (CONTACT_FIELDS.some(f => errors.value[f])) { activeTab.value = 'contact' }
    else if (hasDirErrors)                               { activeTab.value = 'dirigeants' }
    return
  }

  isSaving.value = true
  try {
    const res     = await axios.post(`${BASE_URL}/entreprises/add_lead`, buildPayload())
    const raw     = res.data?.lead ?? {}
    const adapted = adaptLead(raw, 0)

    toast.success(`Lead créé : ${raw.nom || form.value.nom}`, {
      description: [raw.ville, raw.secteur_activite].filter(Boolean).join(' · ') ||
                   'Nouveau lead ajouté à votre base.',
    })

    emit('created', adapted)
    resetState()
    emit('close')
  } catch (err) {
    const msg = extractError(err)
    apiError.value = msg
    toast.error('Erreur lors de la création', { description: msg })
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.fade-err-enter-active, .fade-err-leave-active { transition: all 0.2s ease; }
.fade-err-enter-from,   .fade-err-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
