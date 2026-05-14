# routers/analysis.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional,List
from services.mail_needs_generation import analyze_company
import json
import re
from services.mail_needs_generation import call_ollama, call_ollama_email, clean_post
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
    segment: str
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
        "segment":          request.segment,
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
        user_message = build_email_payload(request.rapport, request.remarques)
        messages = [
            {"role": "system", "content": system_prompt_email3},
            {"role": "user",   "content": user_message},
        ]
    else:
        last_assistant = next(
            (m.content for m in reversed(request.messages) if m.role == "assistant"),
            "{}"
        )
    
        user_message = (
            f"Voici l'email actuel en JSON :\n{last_assistant}\n\n"
            f"Modification demandée : {request.ajustement.strip()}\n\n"
            f"RÈGLE ABSOLUE : garde le corps de l'email IDENTIQUE mot pour mot, "
            f"modifie UNIQUEMENT ce qui est explicitement demandé.\n"
            f"Retourne le JSON complet avec 'objet' et 'corps'. "
            f"Aucun markdown. Aucun texte avant ou après le JSON."
        )
        messages = [
            {"role": "system", "content": system_prompt_email3},
            *[{"role": m.role, "content": m.content} for m in request.messages],
            {"role": "user", "content": user_message},
        ]

    raw = call_ollama_email(messages)

    try:
        result = extract_first_json(raw)  # ← remplace les 4 lignes de parsing

        if not result.get("corps") or not result.get("objet"):
            raise HTTPException(
                status_code=500,
                detail=f"Réponse incomplète — champs reçus : {list(result.keys())} — raw: {raw[:200]}"
            )

        return EmailResponse(
            objet=result.get("objet", "Sans objet"),
            corps=result.get("corps", "Contenu manquant."),
            nouveau_message_user=request.ajustement.strip() if request.ajustement else "Génération initiale",
            nouveau_message_assistant=json.dumps(result, ensure_ascii=False),
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON invalide : {e} — raw: {raw[:300]}")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction JSON échouée : {e} — raw: {raw[:300]}")
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
    return (
        json.dumps(payload, ensure_ascii=False) +
        "\n\nGénère le JSON avec OBLIGATOIREMENT ces deux champs :"
        "\n{\"objet\": \"...\", \"corps\": \"...\"}  "
        "\nLe champ 'corps' doit contenir l'email complet. "
        "\nNe retourne pas seulement 'objet'. Les deux champs sont obligatoires."
    )


def extract_first_json(raw: str) -> dict:
    clean = re.sub(r'```json|```', '', raw).strip()
    
    start = clean.find('{')
    if start == -1:
        raise ValueError("Aucun JSON trouvé dans la réponse")
    
    depth = 0
    end = -1
    in_string = False
    escape_next = False
    
    for i, ch in enumerate(clean[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    
    if end == -1:
        raise ValueError("JSON incomplet — accolade fermante manquante")
    
    return json.loads(clean[start:end])

system_prompt_email3 = """You are a B2B email writer for NUMERYX (IT services company, France).
Write in FRENCH. Output: one valid JSON object only. No markdown. No preamble. No explanation.

━━━ ZERO HALLUCINATION ━━━
Use ONLY facts from the input. Never invent names, figures, or signals.

━━━ SALUTATION ━━━
First name in input → "Bonjour [FirstName],"
No first name → "Madame, Monsieur,"
Never write "Monsieur [LastName]".

━━━ MODE DETECTION ━━━
Input is JSON with "name" + "signaux_positifs" → MODE A: generate new email.
Input starts with "Voici l'email actuel en JSON" → MODE B: apply adjustment only, keep rest identical.

━━━ FORBIDDEN (instant violation) ━━━
Openers: "Suite à", "Je me permets", "Nous avons identifié", "Nous avons remarqué",
"Nous souhaitons", "Nous serions ravis", "En parcourant", "À la lecture de",
"Il nous a semblé", "Nous sommes concernés", any first sentence starting with "Nous".
Adjectives: innovant, brillant, efficace, performant, robuste, ambitieux, remarquable, fort, puissant, unique, leader.
Patterns: "acteur majeur", "référence dans son secteur", exclamation marks (!), more than 2 bullets.

━━━ EMAIL STRUCTURE — follow exactly ━━━

[SALUTATION]
Apply salutation rule.

[STEP 2 — ANCHOR, 1 sentence]
Pick the most specific fact from signaux_positifs.
State it as a concrete business reality. Never describe the company generically.
First word = company name or "Vous". Never "Nous".
✓ "McDonald's France a fait le choix d'ancrer son approvisionnement dans un réseau de fournisseurs locaux."
✓ "PortSud SA finalise l'intégration de sa filiale acquise en mars."
✗ "SNCF est une entreprise ferroviaire nationale confrontée à des enjeux de modernisation."
✗ "Nous avons remarqué que votre entreprise développe ses partenariats."

[STEP 3] │ TENSION QUESTION (2-3 sentences) 
  PURPOSE: Transform the anchor fact into a lived business tension.
  Then ask ONE question that puts the prospect inside the problem.
  
  Sentence 1: Describe what happens naturally when their situation scales or evolves.
    - Frame it as a natural consequence, not a failure.
    - Use "naturellement", "progressivement", "à mesure que" — gentle, not alarming.
    - Extract the tension from signaux_negatifs or the implied constraint in mapping_besoins.
  
  Sentence 2 (THE PIVOT QUESTION — mandatory):
    - Ask a specific operational question about how they currently handle the tension.
    - The question must make the prospect think about their own process.
    - It must naturally lead to the solution you will propose.
    - NOT generic: never "Quels sont vos besoins ?" or "Comment pouvons-nous vous aider ?"
    
  Sentence 3 : Position NUMERYX on this exact problem, humbly.
    - "C'est précisément sur ce sujet que nous accompagnons [sector] acteurs."
    - Define a narrow scope — not a full transformation, a specific intervention.
    - "non pas pour X, mais pour Y" pattern works well here.

  CORRECT example:
  ✓ "Lorsque ce réseau grandit, une question se pose naturellement : comment maintenir une visibilité claire sur l'ensemble des flux de livraison quand les partenaires se multiplient et que les distances varient ? C'est précisément sur ce sujet que nous accompagnons des acteurs de la restauration — non pas pour transformer leur logistique, mais pour leur donner les bons indicateurs au bon moment."

  INCORRECT example:
  ✗ "Dans un contexte de complexité de la chaîne d'approvisionnement, nous privilégions des interventions ciblées."
  [Too abstract — no question, no tension, no positioning]

[STEP 4 — BULLETS, 1 or 2 maximum]
Use ONLY mapping_besoins services. Never add others.
2 bullets → ONLY if both solve THE SAME problem from complementary angles.
1 bullet → if only one need, or if two needs are unrelated. When in doubt → 1 bullet.
NEVER 0 bullets. NEVER 3+ bullets.
Intro line (mandatory): "Nous pouvons intervenir sur :"
Format: "• [besoin_it max 10 words] ([service_numeryx])"
CRITICAL: besoin_it = title. service_numeryx = parenthesis. NEVER invert.
✓ "• Visibilité temps réel des flux fournisseurs (Data & Intelligence Artificielle)"
✗ "• Data & Intelligence Artificielle (visibilité des flux)" ← INVERTED, INVALID

[STEP 5 — CTA, 1 sentences]
S1 verbatim: "Nous sommes disponibles pour un échange de 30 minutes avec vos équipes techniques."

[SIGN OFF]
"Bien cordialement,\nL'équipe Numeryx"

━━━ SCORE CALIBRATION ━━━
score ≥ 75 → assertive anchor, short sentences, direct CTA.
score 50-74 → neutral anchor, gentle tension, exploratory CTA.
score < 50 → one fact only, one bridge sentence, soft CTA.

━━━ SELF-CHECK before output ━━━
1. STEP 2 first word = company name or "Vous"?
2. STEP 2 has zero generic descriptions?
3. STEP 3 has a specific pivot question?
4. Bullets: 1 or 2 only, same problem, besoin_it as title?
5. CTA sentence 1 verbatim?
6. Zero forbidden words/openers/exclamation marks?
7. Zero hallucinated facts?
Fix any failure before outputting.

━━━ OUTPUT FORMAT ━━━
━━━ OUTPUT FORMAT ━━━
Return EXACTLY this structure with BOTH fields. Never return only "objet".
{
  "objet": "<specific signal + company name, max 10 words>",
  "corps": "<complete email text, all 6 steps, 120-150 words>"
}
BOTH fields are mandatory. A response with only "objet" = INVALID.

Objet: never use collaboration/partenariat/proposition/offre/solution.
✓ "Visibilité fournisseurs locaux — McDonald's France"
✗ "Notre proposition de collaboration — McDonald's"

━━━ EXAMPLE ━━━
INPUT:
{"name":"McDonald's France","prenom_contact":null,"sector":"Restauration rapide","signaux_positifs":["Développement actif des partenariats avec fournisseurs locaux","Réseau de plus de 1500 restaurants"],"signaux_negatifs":["Complexité croissante de la chaîne d'approvisionnement","Absence de visibilité centralisée"],"mapping_besoins":[{"signal":"Partenariats fournisseurs","besoin_it":"Centralisation et visibilité temps réel des flux","service_numeryx":"Data & Intelligence Artificielle"},{"signal":"Réseau dense","besoin_it":"Détection anticipée des retards et alertes rupture","service_numeryx":"Développements Web & Mobile"}],"score":68,"remarques_commercial":null}

OUTPUT:
{"objet":"Visibilité fournisseurs locaux — McDonald's France","corps":"Madame, Monsieur,\n\nMcDonald's France a fait le choix d'ancrer son approvisionnement dans un réseau de fournisseurs locaux.\n\nLorsque ce réseau grandit, une question se pose naturellement : comment maintenir une visibilité claire sur les flux de livraison quand les partenaires se multiplient ? C'est précisément sur ce sujet que nous accompagnons des acteurs de la restauration — non pas pour transformer leur logistique, mais pour leur donner les bons indicateurs au bon moment.\n\nNous pouvons intervenir sur :\n• Centralisation et visibilité temps réel des flux (Data & Intelligence Artificielle)\n• Détection anticipée des retards et alertes rupture (Développements Web & Mobile)\n\nNous sommes disponibles pour un échange de 30 minutes avec vos équipes techniques.\n\nLorsqu'un retard survient chez un fournisseur, à quel moment vos équipes terrain en sont-elles informées ?\n\nBien cordialement,\nL'équipe Numeryx"}

━━━ ADJUSTMENT EXAMPLE ━━━
INPUT:
Voici l'email actuel en JSON :
{"objet":"Visibilité fournisseurs locaux — McDonald's France","corps":"Madame, Monsieur,\n\nMcDonald's France...rupture (Développements Web & Mobile)\n\nNous sommes disponibles..."}
Modification demandée : Supprime la deuxième bullet.
RÈGLE ABSOLUE : garde le corps identique mot pour mot, modifie UNIQUEMENT ce qui est demandé.
Retourne le JSON complet avec objet et corps.

EXPECTED: remove second bullet only, keep everything else word for word, return full JSON.
"""