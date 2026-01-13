import os
from typing import Dict, Any, Optional, List

from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

_client: Optional[OpenAI] = None


def get_client() -> Optional[OpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def _norm_money(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)) and v > 0:
        # Keep it simple; do not force formatting with commas (QC audiences vary)
        return str(int(v)) if float(v).is_integer() else str(v)
    s = str(v).strip()
    return "" if s in ("0", "0.0", "None", "null") else s


def _norm_km(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float)) and v > 0:
        return str(int(v)) if float(v).is_integer() else str(v)
    s = str(v).strip()
    return "" if s in ("0", "0.0", "None", "null") else s


def _pick_year_from_title(title: str) -> str:
    # Optional: try to find a 4-digit year in the title (e.g., 2022)
    import re
    m = re.search(r"\b(19\d{2}|20\d{2})\b", title or "")
    return m.group(1) if m else ""


def _characteristics(vehicle: Dict[str, Any]) -> List[str]:
    """
    Accept either:
    - vehicle["characteristics"] as list[str]
    - vehicle["features"] as list[str]
    - vehicle["notes"] as str (we won't split aggressively; we keep notes separate)
    """
    chars = vehicle.get("characteristics")
    if isinstance(chars, list):
        return [str(x).strip() for x in chars if str(x).strip()]

    feats = vehicle.get("features")
    if isinstance(feats, list):
        return [str(x).strip() for x in feats if str(x).strip()]

    return []


def build_user_prompt(vehicle: Dict[str, Any], max_chars: Optional[int], channel: str, profile: str) -> str:
    title = (vehicle.get("title") or "").strip()
    year = str(vehicle.get("year") or "").strip() or _pick_year_from_title(title)
    price = _norm_money(vehicle.get("price"))
    km = _norm_km(vehicle.get("km"))
    stock = (vehicle.get("stock") or "").strip()
    location = (vehicle.get("location") or "").strip()
    trim = (vehicle.get("trim") or vehicle.get("version") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    notes = (vehicle.get("notes") or vehicle.get("description") or "").strip()
    chars = _characteristics(vehicle)

    # Build characteristics line (short, readable)
    chars_line = ", ".join(chars) if chars else ""

    # The “anti-bullshit” prompt, structured like the user’s manual questions.
    base = f"""
Tu es un vendeur automobile expérimenté au Québec.
Tu écris des annonces claires, honnêtes et vendeuses.

RÈGLES ABSOLUES :
- Utilise UNIQUEMENT les informations fournies ci-dessous.
- N’invente AUCUNE caractéristique, option, chiffre, garantie, inspection, ou condition ("comme neuf") si ce n’est pas explicitement fourni.
- Si une information n’est pas fournie, n’en parle pas.
- Style : direct, professionnel, vendeur terrain (pas marketing vide).
- Français québécois neutre.

OBJECTIF :
Transformer une base SIMPLE (faits + caractéristiques) en une annonce STRUCTURÉE et PUNCHY
en mettant en valeur les AVANTAGES CLIENT (bénéfices), pas juste les specs.

STRUCTURE OBLIGATOIRE (Facebook) :
1) Titre accrocheur (court, clair)
2) 4–6 bullets orientés AVANTAGES (à partir des caractéristiques)
3) Bloc “Faits” (année, km, version, prix si présent, stock si présent, localisation si présent)
4) Appel à l’action simple (message privé)

STRUCTURE OBLIGATOIRE (Marketplace) :
- Version plus courte (≤ 800 caractères)
- Titre + bullets + CTA
- Pas de blabla

INTERDICTIONS IMPORTANTES :
- Si aucune capacité de remorquage chiffrée n’est fournie → ne donne PAS de chiffre.
  Tu peux dire “capacité de remorquage solide (selon équipement)” sans chiffre.
- Si aucune puissance moteur chiffrée n’est fournie → ne donne PAS de hp/lb-pi.
- Ne mentionne pas le VIN sauf s’il est explicitement fourni.
- Ne mentionne pas de financement, taxes, échange, livraison, etc. sauf si c’est fourni.

DONNÉES FOURNIES :
Profil: {profile}
Canal: {channel}

Titre : {title or "-"}
Année : {year or "-"}
Kilométrage : {km or "-"}
Prix : {price or "-"}
Version : {trim or "-"}
Stock : {stock or "-"}
Localisation : {location or "-"}
Caractéristiques : {chars_line or "-"}
Notes libres : {notes or "-"}
VIN : {vin or "-"}
""".strip()

    if max_chars:
        base += f"\n\nCONTRAINTE: Maximum {max_chars} caractères (incluant espaces)."

    base += "\n\nFORMAT DE SORTIE : Texte prêt à publier, sans explication, sans balises."
    return base


def generate_ad_text(vehicle: Dict[str, Any], profile: str, max_chars: Optional[int] = None) -> str:
    """
    Generates an AI-enhanced ad text based on a simple structured base.
    - profile: truck/suv/exotic/default (your existing classifier output)
    - max_chars: use 800 for Marketplace, None for Facebook (or another limit if you want)
    """
    client = get_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY non défini")

    # Decide channel label (purely instructive)
    channel = "marketplace" if (max_chars is not None and max_chars <= 900) else "facebook"

    system_prompt = DG_SYSTEM_PROMPTS.get(profile, DG_SYSTEM_PROMPTS["default"])
    user_prompt = build_user_prompt(vehicle, max_chars=max_chars, channel=channel, profile=profile)

    resp = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    text = (resp.choices[0].message.content or "").strip()

    # Hard safety: if model ignores max_chars, trim as last resort (better than failing CI)
    if max_chars and len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"

    return text


# -------------------------
# SYSTEM PROMPTS (tone only)
# -------------------------

DG_SYSTEM_PROMPTS = {
    "truck": (
        "Tu es Daniel Giroux, vendeur automobile expérimenté à Saint-Georges (Beauce).\n"
        "Ton style est direct, confiant, vendeur mais crédible.\n"
        "Tu écris pour Facebook Marketplace.\n"
        "Pas d'exagération, pas d'invention.\n"
        "Accent sur robustesse, utilité, valeur réelle."
    ),
    "suv": (
        "Tu es Daniel Giroux, vendeur automobile.\n"
        "Style rassurant, pratique, orienté famille et polyvalence.\n"
        "Clair, structuré, facile à lire sur mobile.\n"
        "Aucune invention."
    ),
    "exotic": (
        "Tu es un vendeur automobile haut de gamme.\n"
        "Style sobre, exclusif, élégant.\n"
        "Phrases courtes. Ton premium.\n"
        "Aucun emoji inutile. Aucun argument inventé."
    ),
    "default": (
        "Tu es Daniel Giroux, vendeur automobile.\n"
        "Style clair, humain, vendeur.\n"
        "Optimisé pour
