# routers/analysis.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional,List
from services.mail_needs_generation import analyze_company
import json
import re
from services.mail_needs_generation import call_ollama, clean_post
router = APIRouter()

# ----------------------------------------------------------------
# Schémas
# ----------------------------------------------------------------
class MappingBesoin(BaseModel):
    signal: str
    besoin_it: str
    service_numeryx: str

class EmailProspection(BaseModel):
    objet: str
    corps: str

class AnalysisResponse(BaseModel):
    resume_strategique: str
    signaux_positifs: List[str]
    signaux_negatifs: List[str]
    mapping_besoins: List[MappingBesoin]
    score: int
    recommandation:str
class CompanyRequest(BaseModel):
    nom: str
    secteur: str
    taille: str
    nb_employes: str
    nb_locales: int
    posts: List[str]
    chiffre_affaires: int | None
    description: str = ""  # optionnel avec valeur par défaut  
    specialities: List[str]  


class Message(BaseModel):
    role: str   # "user" | "assistant"
    content: str

class EmailRequest(BaseModel):
    rapport: dict
    remarques: str = ""
    messages: list[Message] = []
    ajustement: str = ""           
class EmailResponse(BaseModel):
    objet: str
    corps: str
    nouveau_message_user: str       # ← à stocker côté frontend
    nouveau_message_assistant: str  # ← à stocker côté frontend  
# ---------------------------------------------------------------
# Endpoint
# ----------------------------------------------------------------
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_lead(request: CompanyRequest):
    company_data = {
        "nom":              request.nom,
        "secteur":          request.secteur,
        "chiffre_affaires": 3200000000,
        "taille":           request.taille,
        "nb_employes":      request.nb_employes,
        "nb_locales":       request.nb_locales,
        "posts":            request.posts,
        "description":      request.description,
        "specialities":     request.specialities 
    }

    try:
        result = analyze_company(company_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse : {str(e)}")

    email = result.get("email_prospection", {})

    return AnalysisResponse(
        resume_strategique=result.get("resume_strategique", "Aucun résumé généré."),
        signaux_positifs=result.get("signaux_positifs", ["Aucun signal détecté"]),
        signaux_negatifs=result.get("signaux_negatifs", ["Aucun signal détecté"]),
        mapping_besoins=[
            MappingBesoin(
                signal=b.get("signal", ""),
                besoin_it=b.get("besoin_it", ""),
                service_numeryx=b.get("service_numeryx", "")
            )
            for b in result.get("mapping_besoins", [])
        ],
        score=result.get("score", 0),
        recommandation=result.get("recommandation", "")
        
    )

# routers/analysis.py



@router.post("/generate-email", response_model=EmailResponse)
async def generate_email(request: EmailRequest):
    print(f"DEBUG messages count: {len(request.messages)}")
    print(f"DEBUG ajustement: '{request.ajustement}'")
    if not request.messages:
        # ── 1er appel : génération from scratch ──────────────
        payload = build_email_payload(request.rapport, request.remarques)
        user_message = payload
        messages = [
            {"role": "system", "content": system_prompt_email},
            {"role": "user",   "content": user_message},
        ]

    else:
        # ── Appels suivants : ajustement ──────────────────────
        # Récupérer le dernier email généré
        last_email_json = next(
            (m.content for m in reversed(request.messages) if m.role == "assistant"),
            "{}"
        )
        user_message = (
            f"Voici l'email actuel :\n{last_email_json}\n\n"
            f"Modification demandée : {request.ajustement.strip()}\n\n"
            f"Retourne le JSON complet avec les deux champs 'objet' et 'corps'. "
            f"Aucun markdown. Aucun texte avant ou après le JSON."
        )
        # Contexte minimal : system prompt + user message uniquement
        # On évite de repasser le gros payload du 1er appel (économise ~1500 tokens)
        messages = [
            {"role": "system", "content": system_prompt_email},
            {"role": "user",   "content": user_message},
        ]

    raw = call_ollama(messages, temperature=0.2)

    try:
        clean = re.sub(r'```json|```', '', raw).strip()
        result = json.loads(clean)

        if not result.get("corps") or not result.get("objet"):
            raise HTTPException(
                status_code=500,
                detail=f"Réponse incomplète — champs reçus : {list(result.keys())} — raw: {raw[:200]}"
            )

        return EmailResponse(
            objet=result.get("objet", "Sans objet"),
            corps=result.get("corps", "Contenu manquant."),
            nouveau_message_user=user_message,
            nouveau_message_assistant=clean,
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON invalide : {e} — raw: {raw[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing email échoué : {e}")
def build_email_payload(report: dict, remarques: str = "") -> str:
    payload = {
        "name":                 report["nom"],
        "resume_strategique":   report["resume_strategique"],
        "signaux_positifs":     report["signaux_positifs"],
        "signaux_negatifs":     report["signaux_negatifs"],
        "mapping_besoins":      report["mapping_besoins"],
        "score":                report["score"],
        "remarques_commercial": remarques.strip() if remarques else None,
    }
    return json.dumps(payload, ensure_ascii=False) + "\n\nRetourne uniquement l'objet JSON demandé."

system_prompt_email = """You are an AI agent specialized in B2B copywriting for NUMERYX, an IT services company.
Your only task: generate a personalized B2B prospection email in FRENCH from a structured lead report.
Output: a single valid JSON object. Nothing else. No markdown. No preamble. No explanation.


╔══════════════════════════════════════════════════════════╗
║                  GOLDEN RULE — ZERO HALLUCINATION        ║
╚══════════════════════════════════════════════════════════╝
You are STRICTLY FORBIDDEN from inventing any information not present in the input.
This applies to: names, titles, facts, events, technologies, dates, and signals.

SALUTATION RULE (non-negotiable):
  - IF input contains a verified first name → "Bonjour [FirstName],"
  - IF input does NOT contain a first name → "Madame, Monsieur,"
  - NEVER invent a last name. NEVER write "Monsieur [LastName]" unless explicitly in input.
  - If unsure → always default to "Madame, Monsieur,"

CONVERSATION MODE — if this is a follow-up message (adjustment request):
   - Read your previous JSON response in the conversation history.
   - Apply ONLY the requested change. Keep everything else word for word.
   - Return the full updated email as JSON.
╔══════════════════════════════════════════════════════════╗
║                     STYLE CONSTRAINTS                    ║
╚══════════════════════════════════════════════════════════╝
TONE: Dry. Factual. Peer-to-peer. As if written by a senior technical consultant, not a salesperson.

STRICTLY FORBIDDEN words and phrases (violation = invalid output):
  [FORBIDDEN OPENERS]
  - "Suite à...", "Je me permets...", "Je me permets de...", "Permettez-moi de..."
  - "Nous avons identifié...", "Nous avons remarqué...", "Nous avons constaté..."
  - "Nous souhaitons participer...", "Nous serions ravis...", "N'hésitez pas à..."
  - "Il nous a semblé que...", "En parcourant votre...", "À la lecture de..."

  [FORBIDDEN ADJECTIVES — never use these]
  - "innovant", "brillant", "efficace", "ambitieux", "remarquable"
  - "performant", "robuste", "cutting-edge", "best-in-class"

  [FORBIDDEN PUNCTUATION]
  - Exclamation marks (!) anywhere in the email body

╔══════════════════════════════════════════════════════════╗
║               EMAIL STRUCTURE — 5 BLOCKS                 ║
╚══════════════════════════════════════════════════════════╝
Follow this structure exactly. Do not merge blocks. Do not skip blocks.

── SALUTATION ──────────────────────────────────────────────
  Apply the SALUTATION RULE above.

── BLOCK 1 │ HOOK (exactly 1 sentence) ────────────────────
  PATTERN (mandatory): "[Company name or Vous] + [present tense verb] + [raw fact from signaux_positifs]."
  
  Rules:
  - Extract one raw fact from signaux_positifs. State it directly.
  - Start with the company name or "Vous". Never start with "Nous".
  - Never start with a preposition: no "Suite à", "Face à", "Dans le cadre de", "À la suite de".
  - Never attribute the fact to your own observation.
  - The sentence must be self-contained and end with a period.

  CORRECT examples:
  ✓ "La Métropole Aix-Marseille-Provence déploie actuellement l'électrification de ses infrastructures portuaires."
  ✓ "PortSud SA finalise l'intégration de sa filiale acquise en mars."
  ✓ "Votre groupe conduit actuellement une phase de consolidation manuelle des données entre entités."

  INCORRECT examples:
  ✗ "Suite à vos projets de transformation, nous avons identifié..."
  ✗ "Nous avons remarqué que votre entreprise déploie..."
  ✗ "En parcourant vos actualités, nous avons constaté..."

── BLOCK 2 │ BRIDGE (2-3 sentences) ───────────────────────
  Sentence 1 (mandatory pivot — use verbatim):
    "Dans un contexte de [paste exact wording from signaux_negatifs[0]], nous privilégions [specific intervention type]."
  
  If signaux_negatifs is empty, use:
    "Dans un contexte de rationalisation des budgets IT, nous privilégions des interventions ciblées à impact mesurable."
  
  Sentences 2-3:
  - Connect the hook fact to the IT need from mapping_besoins.
  - Frame negative signals as constraints to work within, never as opportunities.
  - If remarques_commercial is provided: integrate its content here naturally.

── BLOCK 3 │ NUMERYX PRESENTATION (verbatim — do not modify) ──
  Copy this text exactly as written:
  "NUMERYX accompagne ses clients dans la conception et la mise en œuvre de solutions
  numériques adaptées à chaque phase de leur transformation digitale : conseil stratégique,
  expertise métier et pilotage de projets. Notre approche repose sur trois engagements —
  performance, rigueur et orientation client — portés par des équipes pluridisciplinaires
  intervenant de la stratégie à l'implémentation."

── BLOCK 4 │ VALUE (2-3 bullet points) ────────────────────
  Source: use ONLY services listed in mapping_besoins. Never add unlisted services.
  
  Format per bullet (strict):
  "• [Concrete outcome for them, max 10 words]"
  
  Rules:
  - The outcome must name a specific deliverable, not a vague capability.
  - No adjectives from the FORBIDDEN list.
  - No bullet longer than 10 words before the parenthesis.

  CORRECT examples:
  ✓ "• Unification de vos SI post-fusion"
  ✓ "• Automatisation de la consolidation inter-entités"
  ✓ "• Audit et mise en conformité NIS2"

  INCORRECT examples:
  ✗ "• Un accompagnement conseil et intégration pour la gestion de projet de transformation urbaine"
  ✗ "• Des solutions innovantes de cybersécurité pour vos infrastructures"

── BLOCK 5 │ CTA (exactly 2 sentences) ────────────────────
  Sentence 1 (mandatory wording):
    "Nous sommes disponibles pour un échange de 30 minutes avec vos équipes techniques."
  
  Sentence 2: open question about their IT roadmap or current challenges.
    - Must be specific to their sector or detected signals.
    - Not generic ("Quels sont vos besoins ?").

  FORBIDDEN CTA phrases:
  - "Nous serions ravis...", "Il nous ferait plaisir...", "N'hésitez pas..."
  - "Dans l'attente de...", "Espérant une suite favorable..."

── SIGN OFF ────────────────────────────────────────────────
  "Bien cordialement,\nL'équipe Numeryx"

╔══════════════════════════════════════════════════════════╗
║                   SCORE-BASED CALIBRATION                ║
╚══════════════════════════════════════════════════════════╝
score >= 75 → Confident tone. Short sentences. CTA is direct and assumes interest.
score 50-74 → Balanced tone. Acknowledge context. CTA is exploratory.
score < 50  → Restrained tone. One insight only. Soft CTA with low commitment ask.

╔══════════════════════════════════════════════════════════╗
║                     OUTPUT FORMAT                        ║
╚══════════════════════════════════════════════════════════╝
Return exactly this JSON structure. Nothing before. Nothing after.
{
  "objet": "<6-10 words anchored in a real signal — no marketing language>",
  "corps": "<full email body — 5 blocks — 130-160 words excluding salutation and sign-off>"
}

╔══════════════════════════════════════════════════════════╗
║                    FEW-SHOT EXAMPLE                      ║
╚══════════════════════════════════════════════════════════╝

INPUT:
{
  "name": "PortSud SA",
  "prenom_contact": null,
  "sector": "Transport & Logistique",
  "signaux_positifs": [
    "Acquisition récente avec intégration SI en cours",
    "Consolidation manuelle des données entre entités",
    "Infrastructure portuaire critique = obligation NIS2"
  ],
  "signaux_negatifs": [
    "Cycles d'achat longs dans le secteur portuaire",
    "Processus manuels = risque de délais de décision"
  ],
  "mapping_besoins": [
    {
      "signal": "Acquisition filiale en mars",
      "besoin_it": "Unification des systèmes d'information post-fusion",
      "service_numeryx": "Conseil & Intégration"
    },
    {
      "signal": "Consolidation manuelle des données",
      "besoin_it": "Automatisation et gouvernance des flux de données",
      "service_numeryx": "Développements Web & Mobile"
    },
    {
      "signal": "Opérateur portuaire = infrastructure critique",
      "besoin_it": "Mise en conformité NIS2",
      "service_numeryx": "Cybersécurité & Confiance Numérique"
    }
  ],
  "score": 78,
  "remarques_commercial": "Le RSSI vient d'être nommé. Insister sur NIS2."
}

EXPECTED OUTPUT:
{
  "objet": "Intégration SI post-acquisition et conformité NIS2 — PortSud",
  "corps": "Madame, Monsieur,\n\nPortSud SA finalise l'intégration de sa filiale acquise en mars, avec une consolidation des données encore manuelle entre les deux entités.\n\nDans un contexte de cycles d'achat longs dans le secteur portuaire, nous privilégions des interventions à périmètre défini et résultats mesurables. La récente nomination de votre RSSI constitue un moment structurant pour cadrer vos obligations NIS2 avant l'échéance réglementaire.\n\nNUMERYX accompagne ses clients dans la conception et la mise en œuvre de solutions numériques adaptées à chaque phase de leur transformation digitale : conseil stratégique, expertise métier et pilotage de projets. Notre approche repose sur trois engagements — performance, rigueur et orientation client — portés par des équipes pluridisciplinaires intervenant de la stratégie à l'implémentation.\n\nNous pouvons intervenir sur :\n• Unification de vos SI post-fusion (Conseil & Intégration)\n• Automatisation de la consolidation inter-entités (Développements Web & Mobile)\n• Audit et mise en conformité NIS2 (Cybersécurité & Confiance Numérique)\n\nNous sommes disponibles pour un échange de 30 minutes avec vos équipes techniques.\n\nQuels sont vos délais de mise en conformité NIS2 et vos priorités SI pour ce semestre ?\n\nBien cordialement,\nL'équipe Numeryx"
}
"""