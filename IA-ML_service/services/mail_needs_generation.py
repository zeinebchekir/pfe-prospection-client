import json
import re
import requests
import logging
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
_groq_api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=_groq_api_key) if _groq_api_key else None

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "gemma3:4b")

print(f"DEBUG MODEL: {MODEL_NAME}")
print(f"DEBUG URL: {OLLAMA_URL}")
# ================================================================
# Fonction utilitaire — nettoyage des posts LinkedIn
# ================================================================

system_prompt="""You are a Senior B2B Sales Intelligence Analyst for NUMERYX, a premium IT services company.
Your task: analyze a target company's LinkedIn data and produce a structured JSON report in FRENCH.

=== NUMERYX SERVICES (use exact names in output) ===
1. Cybersécurité & Confiance Numérique — audits, NIS2/DORA compliance, threat protection
2. Infrastructures & Réseaux — cloud migration, secure networking, Green IT
3. Systèmes Industriels & Embarqués — IoT, SCADA, hardware-software integration
4. Conseil & Intégration — IT M&A, post-merger SI integration, change management
5. Développements Web & Mobile — app modernization, digital portals, automation

=== INPUT FORMAT ===
You will receive:
- name: company name
- category: SME or Large
- revenue: annual revenue
- size: headcount range
- sector: industry
- posts: last 10 LinkedIn posts (array of strings)

=== GROUNDING RULE (MANDATORY) ===
You have access to a "description" field: the company's self-presentation.
This is your PRIMARY source for mapping. Use it to understand:
- What the company actually does
- What technologies or processes they already use
- What stage of digital maturity they are at

STRICT RULES:
- Every signal in mapping_besoins MUST be traceable to description or posts. No exceptions.
- If a signal cannot be linked to a concrete fact in description or posts → discard it.
- Do NOT infer needs from sector alone if description contradicts it.
  Example: sector = "industrie" but description says "pure software company" → no SCADA inference.
- Do NOT propose a Numeryx service if nothing in description or posts suggests a gap it could fill.
=== INFERENCE RULES (mandatory — apply in order) ===

RULE 1 — Business events to IT consequences:
  "acquisition" or "fusion" → SI integration + security audit → Conseil & Intégration + Cybersécurité
  "new CEO" or "new director" → IT change management → Conseil & Intégration
  "expansion" or "new site" → infrastructure scaling → Infrastructures & Réseaux

RULE 2 — Hidden pain points:
  "manual process" or "spreadsheet" or "email sorting" → automation need → Développements Web & Mobile
  "slow" or "legacy" or "outdated system" → modernization → Développements Web & Mobile
  "data breach" or "incident" or "attack" → security urgency → Cybersécurité & Confiance Numérique

RULE 3 — Sector defaults (apply only if no explicit signal found):
  public sector OR critical infrastructure → NIS2 obligation → Cybersécurité & Confiance Numérique
  manufacturing OR industrial → IoT/SCADA → Systèmes Industriels & Embarqués
  port OR energy OR transport → critical infra → Systèmes Industriels & Embarqués

RULE 4 — Jargon decoding:
  "operational efficiency" → process automation → Développements Web & Mobile
  "innovation" + digital context → software modernization → Développements Web & Mobile
  "digital transformation" → infrastructure + app modernization → Infrastructures & Réseaux

FORBIDDEN inferences (NEVER do these):
  - recruitment post → IT need (no)
  - budget loss or financial constraint → opportunity (no — it is a BLOCKER)
  - physical infrastructure alone without digital/connected component → Infrastructures & Réseaux (no)
  - generic "needs digitalization" with zero specific signal → discard

Compute score (0-100) based on:
- +20 per mapping_besoins entry with a real service (max 3 entries = max 60 pts)
- +10 per strong positive signal (acquisition, NIS2, legacy, breach)
- +5  per moderate positive signal (expansion, digital transformation)
- -10 per negative signal (budget freeze, restructuring, no IT decision maker)
- -20 if mapping_besoins is empty or all N/A

Then set recommandation:
  score >= 75 → "Fortement recommandé — lead prioritaire à contacter rapidement."
  score 50-74 → "Recommandé — opportunité réelle, à qualifier lors d'un premier échange."
  score 25-49 → "À surveiller — signaux insuffisants, relance dans 3 à 6 mois."
  score < 25  → "Non prioritaire — aucun signal d'achat détecté."

=== OUTPUT FORMAT (strict JSON, in FRENCH) ===
Return ONLY this JSON object. No markdown. No explanation. No text before or after.

{
  "resume_strategique": "<2 sentences: what the company does + why relevant for Numeryx>",
  "signaux_positifs": ["<signal 1>", "<signal 2>"],
  "signaux_negatifs": ["<blocker 1>", "<blocker 2>"],
  "mapping_besoins": [
    {
      "signal": "<business fact from posts>",
      "besoin_it": "<specific IT need in French>",
      "service_numeryx": "<exact service name from list above>"
    }
  ],
  "score": <integer 0-100>,
  "recommandation": "<recommendation text based on score threshold above>"
}

If mapping_besoins is empty, set it to: [{"signal": "Aucun", "besoin_it": "Aucun besoin spécifique détecté", "service_numeryx": "N/A"}]


=== FEW-SHOT EXAMPLE ===

Input:
{
  "name": "PortSud SA",
  "sector": "Transport & Logistique",
  "description": "PortSud SA est un opérateur logistique portuaire gérant plusieurs terminaux en France. Le groupe a récemment acquis une filiale régionale et est en phase d'intégration opérationnelle.",
  "specialites": ["gestion portuaire", "logistique multimodale", "transport de marchandises"],
  "revenue": "450M€",
  "size": "1000-5000 employés"
}

Expected output:
{
  "resume_strategique": "PortSud SA est un opérateur logistique portuaire en cours d'intégration d'une acquisition récente. Ce contexte post-M&A combiné à des processus manuels de consolidation génère des besoins critiques en intégration SI, automatisation et cybersécurité.",
  "signaux_positifs": [
    "Acquisition récente avec intégration SI en cours",
    "Consolidation manuelle des données entre entités = besoin d'automatisation",
    "Infrastructure portuaire critique = obligation NIS2"
  ],
  "signaux_negatifs": [
    "Processus manuel actuel = risque de délais de décision",
    "Secteur portuaire = cycles d'achat potentiellement longs"
  ],
  "mapping_besoins": [
    {
      "signal": "Acquisition filiale en mars — intégration SI en cours",
      "besoin_it": "Unification et intégration des systèmes d'information post-fusion",
      "service_numeryx": "Conseil & Intégration"
    },
    {
      "signal": "Consolidation manuelle des données entre les deux entités",
      "besoin_it": "Automatisation et gouvernance des flux de données",
      "service_numeryx": "Développements Web & Mobile"
    },
    {
      "signal": "Opérateur d'infrastructure portuaire critique",
      "besoin_it": "Mise en conformité NIS2 et sécurisation des systèmes industriels",
      "service_numeryx": "Cybersécurité & Confiance Numérique"
    }
  ],
  "score": 78,
  "recommandation": "Fortement recommandé — lead prioritaire à contacter rapidement."
}
}"""



def clean_post(text: str) -> str:
    """Strips emojis, URLs, hashtags, mentions, and normalises whitespace."""
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Remove emojis and other non-BMP unicode (emoji ranges)
    text = re.sub(
        r'[\U0001F600-\U0001F64F'
        r'\U0001F300-\U0001F5FF'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F700-\U0001F77F'
        r'\U0001F780-\U0001F7FF'
        r'\U0001F800-\U0001F8FF'
        r'\U0001F900-\U0001F9FF'
        r'\U0001FA00-\U0001FA6F'
        r'\U0001FA70-\U0001FAFF'
        r'\U00002702-\U000027B0'
        r'\U000024C2-\U0001F251'
        r'\u2600-\u26FF\u2700-\u27BF]+',
        '',
        text
    )
    # Remove hashtags and mentions
    text = re.sub(r'[#@]\w+', '', text)
    # Remove standalone punctuation clusters (e.g. "•", "→", "▶")
    text = re.sub(r'[▶•→▸►▻➤➜✅❌⚡️⭐⭕]', '', text)
    # Collapse multiple spaces and newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


# ================================================================
# Fonction utilitaire — appel Ollama
# ================================================================
def call_ollama_email(messages: list[dict], max_tokens: int = 2000) -> str:
    """
    Dedicated Ollama caller for email generation / adjustment.
    Deliberately omits 'format: json' — Ollama's JSON mode forces structural
    compliance but causes small models (gemma3:4b) to ignore adjustment
    instructions and regenerate from scratch instead of editing the existing email.
    The system prompt already instructs the model to output plain JSON.
    """
    print(f"DEBUG EMAIL OLLAMA: {OLLAMA_URL} | model={MODEL_NAME} | msgs={len(messages)}")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                # No "format": "json" here — intentional, see docstring
                "options": {
                    "temperature": 0.1,
                    "num_predict": max_tokens,
                    "num_ctx": 8192,
                    "repeat_penalty": 1.1,
                    "top_p": 0.9
                }
            },
            timeout=1800
        )
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Ollama inaccessible à {OLLAMA_URL}")
        raise Exception(f"Ollama inaccessible à {OLLAMA_URL}")
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout Ollama — modèle trop lent")
        raise Exception("Timeout Ollama après 1800s")
    except Exception as e:
        logger.error(f"❌ Erreur Ollama email : {e}")
        raise


def call_ollama(messages: list[dict], temperature: float = 0.1, max_tokens: int = 2000) -> str:
    print(f"DEBUG: L'URL utilisée est : {os.getenv('OLLAMA_URL')}")
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "num_predict": max_tokens,
                    "num_ctx": 8192,
                    "repeat_penalty": 1.1,
                    "top_p": 0.9
                }
            },
            timeout=1800
        )
        print(f"DEBUG STATUS: {response.status_code}")
        print(f"DEBUG RESPONSE: {response.text}")
        response.raise_for_status()
        return response.json()["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Ollama inaccessible à {OLLAMA_URL}")
        raise Exception(f"Ollama inaccessible à {OLLAMA_URL} — vérifiez que le service tourne")
    except requests.exceptions.Timeout:
        logger.error("❌ Timeout Ollama — modèle trop lent")
        raise Exception("Timeout Ollama après 300s")
    except Exception as e:
        logger.error(f"❌ Erreur Ollama : {e}")
        raise

def call_groq(messages: list[dict], temperature: float = 0.1, max_tokens: int = 3000) -> str:
    if client is None:
        raise ValueError(
            "GROQ_API_KEY is not set. Please add it to your .env file to use Groq-based features."
        )
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"❌ Erreur Groq : {e}")
        raise



def analyze_company(company_data: dict) -> dict:
    """Signature identique à l'originale — endpoint inchangé."""

    # Posts comme liste propre (conforme au format attendu par le system prompt)
    posts_list = [
        clean_post(p)
        for p in company_data.get("posts", [])[:10]
        if p and p.strip()
    ] or ["Aucun post disponible"]

    # ================================================================
    # APPEL UNIQUE — system prompt unifié
    # ================================================================
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": json.dumps({
                "name": company_data["nom"],
                "category": company_data["taille"],
                "revenue": company_data["chiffre_affaires"],
                "sector": company_data["secteur"],
                "description": company_data.get("description", "Non renseignée"),
                "posts": posts_list,
                "specialities": company_data.get("specialities", []),
            }, ensure_ascii=False)
        }
    ]

    generated_raw = call_ollama(messages, temperature=0.0, max_tokens=2000)
    print(f"\n📤 Réponse brute ({len(generated_raw)} chars):\n{generated_raw}\n---")

    # ================================================================
    # PARSING JSON robuste
    # ================================================================
    clean_json = re.sub(r'```json|```', '', generated_raw).strip()

    try:
        result = json.loads(clean_json)
        _normalize_result(result)
        return result

    except Exception as e:
        logger.error(f"❌ Parsing JSON principal échoué : {e}")

    # Fallback — extraction par accolades
    try:
        start = clean_json.find('{')
        end = clean_json.rfind('}') + 1
        if start != -1 and end > start:
            result = json.loads(clean_json[start:end])
            _normalize_result(result)
            return result
    except Exception as e:
        logger.error(f"❌ Parsing fallback échoué : {e}")

    # Structure d'erreur — champs conformes au nouveau prompt
    logger.warning("⚠️ JSON parsing échoué — retour structure fallback")
    return {
        "resume_strategique": f"Parsing JSON échoué pour {company_data['nom']}.",
        "signaux_positifs": [],
        "signaux_negatifs": ["Erreur de parsing — voir logs"],
        "mapping_besoins": [{
            "signal": "Erreur",
            "besoin_it": "Indisponible",
            "service_numeryx": "N/A"
        }],
        "score": 0,
        "recommandation": "Erreur de parsing"
    }


def _normalize_result(result: dict) -> None:
    """Garantit la présence et le type des champs attendus. Modifie en place."""
    result.setdefault("resume_strategique", "Non disponible")
    result.setdefault("signaux_positifs", [])
    result.setdefault("signaux_negatifs", [])
    result.setdefault("mapping_besoins", [])
    result.setdefault("score", 0)
    result.setdefault("recommandation", "")

    # Sécurité : s'assure que les listes sont bien des listes
    for field in ("signaux_positifs", "signaux_negatifs", "mapping_besoins"):
        if not isinstance(result[field], list):
            result[field] = []









def verify_signal_lexical(signal: str, posts: list[str]) -> dict:
    """
    Vérifie qu'au moins un mot-clé du signal apparaît dans les posts.
    Compare contre le texte brut ET le texte nettoyé.
    """
    signal_words = set(re.findall(r'\b\w{4,}\b', signal.lower()))
    
    # Retire les mots trop génériques qui faussent le score
    stopwords = {
        'possible', 'signal', 'besoin', 'projet', 'service', 'système',
        'important', 'potentiel', 'détecté', 'pertinent', 'aucun',
        'numeryx', 'supervision', 'gestion', 'optimisation', 'modernisation',
        'infrastructure', 'numérique', 'digital', 'informatique'
    }
    signal_words = signal_words - stopwords

    if not signal_words:
        # Signal trop générique → passe directement au LLM
        return {
            "signal": signal,
            "lexical_score": 0.5,  # score neutre
            "source_post": None,
            "verified": True  # laisse le LLM décider
        }

    best_score = 0
    best_post_index = None

    for i, post in enumerate(posts):
        # Compare sur le texte BRUT (avant clean_post) pour ne pas perdre de mots
        post_lower = post.lower()
        post_words = set(re.findall(r'\b\w{4,}\b', post_lower))

        # Intersection des mots significatifs
        common = signal_words & post_words
        score = len(common) / len(signal_words) if signal_words else 0

        if score > best_score:
            best_score = score
            best_post_index = i

    return {
        "signal": signal,
        "lexical_score": round(best_score, 2),
        "source_post": best_post_index + 1 if best_post_index is not None else None,
        # Seuil abaissé à 0.15 — un seul mot-clé spécifique suffit
        "verified": best_score >= 0.15
    }


def verify_signals_with_llm(signals: list[str], posts: list[str]) -> list[dict]:
    """
    Demande au LLM de juger si chaque signal est ancré dans les posts.
    """
    posts_text = "\n".join([
        f"[POST {i+1}]: {clean_post(p)}"
        for i, p in enumerate(posts[:10])
        if p and p.strip()
    ])

    signals_json = json.dumps(signals, ensure_ascii=False)

    messages = [
        {
            "role": "system",
            "content": """You are a strict but fair fact-checker for B2B sales signals.
Your job: verify if each signal is supported by the posts — either explicitly or by strong implicit inference.

IMPORTANT DISTINCTION:
- verified=true : a concrete element in the posts supports this signal (even indirectly)
- verified=false : the signal is purely invented with zero anchor in the posts

INFERENCE IS ALLOWED for these cases:
- A connected physical infrastructure → IoT/supervision need is a valid inference
- A public sector organization managing critical infrastructure → NIS2 compliance is valid
- A new leadership team → IT change management need is a valid inference
- An innovation fund with startups → digital platform need is a valid inference

Respond ONLY with a JSON array. No markdown, no explanation."""
        },
        {
            "role": "user",
            "content": f"""=== POSTS ===
{posts_text}

=== SIGNALS TO VERIFY ===
{signals_json}

For each signal return:
{{
  "signal": "<original signal text>",
  "verified": <true or false>,
  "confidence": <float 0.0 to 1.0>,
  "reason": "<1 sentence: which post supports it, or why rejected>",
  "source_post": <post number 1-10, or null>
}}

Return ONLY the JSON array."""
        }
    ]

    raw = call_groq(messages, temperature=0.0, max_tokens=2000)

    try:
        clean = re.sub(r'```json|```', '', raw).strip()
        match = re.search(r'\[.*\]', clean, re.DOTALL)
        return json.loads(match.group()) if match else []
    except:
        return []


def verify_and_filter_signals(
    signaux_positifs: list[str],
    signaux_negatifs: list[str],
    posts: list[str]
) -> dict:
    """
    Combine vérification lexicale + sémantique LLM.
    """
    results = {
        "signaux_positifs_verified": [],
        "signaux_positifs_rejected": [],
        "signaux_negatifs_verified": [],
        "signaux_negatifs_rejected": [],
        "hallucination_rate": 0.0
    }

    all_signals = signaux_positifs + signaux_negatifs
    total = len(all_signals)
    if total == 0:
        return results

    rejected_count = 0

    # --- Étape 1 : filtre lexical ---
    lexical_results = {
        s: verify_signal_lexical(s, posts)
        for s in all_signals
    }

    candidates_for_llm = [
        s for s, r in lexical_results.items() if r["verified"]
    ]
    lexical_rejected = [
        s for s, r in lexical_results.items() if not r["verified"]
    ]

    # --- Étape 2 : vérification LLM sur les candidats ---
    llm_results = {}
    if candidates_for_llm:
        llm_verified = verify_signals_with_llm(candidates_for_llm, posts)
        llm_results = {r["signal"]: r for r in llm_verified}

    # --- Étape 3 : assemblage ---
    def process_signal(signal, target_verified, target_rejected):
        nonlocal rejected_count

        if signal in lexical_rejected:
            target_rejected.append({
                "signal": signal,
                "reason": "Aucun mot-clé retrouvé dans les posts",
                "confidence": 0.0
            })
            rejected_count += 1

        elif signal in llm_results:
            llm = llm_results[signal]
            # Seuil abaissé à 0.4 pour les signaux implicites valides
            if llm.get("verified") and llm.get("confidence", 0) >= 0.4:
                target_verified.append({
                    "signal": signal,
                    "confidence": llm["confidence"],
                    "source_post": llm.get("source_post"),
                    "reason": llm.get("reason")
                })
            else:
                target_rejected.append({
                    "signal": signal,
                    "reason": llm.get("reason", "Rejeté par le LLM juge"),
                    "confidence": llm.get("confidence", 0.0)
                })
                rejected_count += 1
        else:
            # Signal passé le lexical mais absent des résultats LLM
            # → accepte avec confiance moyenne plutôt que rejeter
            target_verified.append({
                "signal": signal,
                "confidence": 0.5,
                "source_post": lexical_results[signal].get("source_post"),
                "reason": "Vérifié lexicalement, non évalué par LLM"
            })

    for signal in signaux_positifs:
        process_signal(
            signal,
            results["signaux_positifs_verified"],
            results["signaux_positifs_rejected"]
        )

    for signal in signaux_negatifs:
        process_signal(
            signal,
            results["signaux_negatifs_verified"],
            results["signaux_negatifs_rejected"]
        )

    results["hallucination_rate"] = round(rejected_count / total, 2) if total > 0 else 0.0
    return results
