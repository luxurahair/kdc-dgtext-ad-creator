# llm.py – Intro AI centrée sur Daniel Giroux
import os
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

_client: Optional[OpenAI] = None


def get_client() -> Optional[OpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or not OpenAI:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def _fmt_money(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        n = int(float(value))
        return f"{n:,}".replace(",", " ") + " $"
    except Exception:
        return str(value).strip()


def _fmt_km(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        n = int(float(value))
        return f"{n:,}".replace(",", " ") + " km"
    except Exception:
        return str(value).strip()


def _vehicle_price(vehicle: Dict[str, Any]) -> str:
    v = vehicle or {}
    raw = v.get("price")
    if raw in (None, ""):
        raw = v.get("price_int")
    return _fmt_money(raw)


def _vehicle_mileage(vehicle: Dict[str, Any]) -> str:
    v = vehicle or {}
    raw = v.get("mileage")
    if raw in (None, ""):
        raw = v.get("km")
    if raw in (None, ""):
        raw = v.get("km_int")
    return _fmt_km(raw)


def _safe_trim(text: str, max_chars: int) -> str:
    txt = (text or "").strip()
    if len(txt) <= max_chars:
        return txt

    phone = "418-222-3939"
    if phone in txt:
        idx = txt.find(phone) + len(phone)
        if idx <= max_chars:
            return txt[:idx].rstrip(" .,!?;:-")

    cut = txt[:max_chars].rstrip(" .,!?;:-")
    return cut + "..."


def generate_ad_text(vehicle: Dict[str, Any], kind: str = "default", max_chars: int = 220) -> str:
    """
    Génère une courte intro AI Facebook, centrée sur Daniel Giroux.
    kind:
      - default
      - price_changed
    """
    client = get_client()
    if not client:
        return ""

    v = vehicle or {}
    title = (v.get("title") or "Véhicule").strip()
    price = _vehicle_price(v)
    mileage = _vehicle_mileage(v)
    stock = str(v.get("stock") or "").strip()
    url = str(v.get("url") or "").strip()
    old_price = _fmt_money(v.get("old_price"))
    new_price = _fmt_money(v.get("new_price"))

    if kind == "price_changed":
        angle = (
            "Le véhicule vient de baisser de prix. "
            "Fais sentir l'opportunité avec un ton vendeur humain, crédible et naturel. "
            "Mentionne clairement l'ancien prix puis le nouveau prix si disponibles."
        )
    else:
        angle = (
            "Mets l'accent sur l'usage réel du véhicule en Beauce, "
            "sur un avantage concret, et donne envie d'écrire à Daniel Giroux."
        )

    system_prompt = f"""
Tu es Daniel Giroux, vendeur automobile chez Kennebec à Saint-Georges (Beauce, Québec) depuis 2009.

Ton style :
- direct
- chaleureux
- crédible
- vendeur humain
- français québécois naturel
- parle en "je" ou "moi"
- jamais au nom de l'entreprise
- jamais robotique
- jamais agressif
- aucune invention

Données disponibles :
- Titre : {title}
- Prix : {price}
- Kilométrage : {mileage}
- Stock : {stock}
- URL : {url}
- Ancien prix : {old_price}
- Nouveau prix : {new_price}

Objectif :
Écris UNE courte accroche Facebook qui sert directement Daniel Giroux.
{angle}

Règles obligatoires :
- maximum {max_chars} caractères
- 1 ou 2 petites phrases maximum
- ton vendeur, naturel, humain
- pas de hashtags
- pas de liste
- pas de jargon
- au plus 1 emoji si ça aide vraiment
- termine avec un appel direct incluant Daniel Giroux 418-222-3939
"""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Génère une accroche courte et vendeuse pour {title}.",
                },
            ],
            max_tokens=90,
            temperature=0.8,
            top_p=0.9,
        )

        txt = (response.choices[0].message.content or "").strip()
        return _safe_trim(txt, max_chars)

    except Exception as e:
        print(f"[ERROR AI] {e}")
        return ""
