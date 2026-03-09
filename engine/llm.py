# llm.py – version 2026 ultra-robuste, sans hallucination, style Daniel Giroux
import os
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Modèle forcé : gpt-4o-mini = rapide + pas cher + bon pour textes courts
DEFAULT_MODEL = "gpt-4o-mini"

_client: Optional[OpenAI] = None

def get_client() -> Optional[OpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not OpenAI:
        print("[WARN LLM] Clé OpenAI absente ou openai non installé")
        return None
    if _client is None:
        try:
            _client = OpenAI(api_key=api_key)
            print("[DEBUG LLM] Client OpenAI créé avec succès")
        except Exception as e:
            print(f"[ERROR LLM] Échec création client OpenAI : {str(e)}")
            return None
    return _client


def generate_ad_text(vehicle: Dict[str, Any], kind: str = "default", max_chars: int = 250) -> str:
    """
    Génère une intro courte et naturelle pour annonce Facebook.
    ZÉRO invention. Base UNIQUEMENT sur vehicle dict.
    """
    client = get_client()
    if not client:
        print("[DEBUG LLM] Pas de client OpenAI → retour vide")
        return ""

    # Extraction sécurisée des données (pas d'erreur si clé manquante)
    title = str(vehicle.get('title') or 'Véhicule').strip()
    price = str(vehicle.get('price') or '').strip()
    mileage = str(vehicle.get('mileage') or '').strip()
    stock = str(vehicle.get('stock') or '').strip()
    url = str(vehicle.get('url') or '').strip()
    features = ', '.join(str(f) for f in (vehicle.get('features') or []))

    # Prompt béton : anti-hallucination, style vendeur Beauce
    system_prompt = f"""
Tu es Daniel Giroux, vendeur automobile chez Kennebec Dodge Chrysler à Saint-Georges, Beauce, Québec.
Ton style : direct, chaleureux, crédible, québécois naturel. Pas d'exagération, pas d'invention.
Tu parles seulement de ce qui est dans les données ci-dessous.

Données véhicule :
- Titre : {title}
- Prix : {price}
- Kilométrage : {mileage}
- Stock : {stock}
- URL : {url}
- Caractéristiques connues : {features or 'aucune'}

Écris UNE SEULE phrase courte (80-150 caractères max) pour introduire l'annonce Facebook.
Exemple acceptable : "Ce Rogue SV 2022 est fiable et parfait pour l’hiver en Beauce avec son AWD !"
Pas de prix inventé, pas de specs inventées, pas de blabla inutile.
"""

    user_prompt = f"Génère intro pour {title} (max {max_chars} caractères)."

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=80,          # Force court
            temperature=0.5,        # Contrôle créativité (0.5 = équilibré)
            top_p=0.9,
        )
        txt = response.choices[0].message.content.strip()
        print(f"[DEBUG LLM] Réponse OpenAI brute : '{txt}'")
        
        # Coupe si trop long
        if len(txt) > max_chars:
            txt = txt[:max_chars].rstrip() + "…"
            
        if not txt:
            print("[DEBUG LLM] OpenAI a renvoyé vide → fallback")
            return ""
            
        return txt

    except Exception as e:
        print(f"[ERROR LLM] Échec appel OpenAI : {str(e)}")
        return ""
