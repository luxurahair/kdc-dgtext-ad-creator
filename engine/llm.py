import os
from typing import Dict

from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

_client = None

def generate_ad_text(vehicle: Dict, profile: str, max_chars: int | None = None) -> str:
    raise RuntimeError("🔥 LLM APPELÉ — SI TU VOIS ÇA, C'EST BRANCHÉ 🔥")


def get_client() -> OpenAI | None:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def generate_ad_text(vehicle: Dict, profile: str, max_chars: int | None = None) -> str:
    client = get_client()
    if not client:
        raise RuntimeError("OPENAI_API_KEY non défini")

    system_prompt = DG_SYSTEM_PROMPTS.get(profile, DG_SYSTEM_PROMPTS["default"])
    user_prompt = build_user_prompt(vehicle, max_chars)

    response = client.chat.completions.create(
        model=DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()


def build_user_prompt(vehicle: Dict, max_chars: int | None) -> str:
    base = (
        f"Infos véhicule :\n"
        f"- Titre : {vehicle.get('title')}\n"
        f"- Prix : {vehicle.get('price')}\n"
        f"- Kilométrage : {vehicle.get('km')}\n"
        f"- Stock : {vehicle.get('stock')}\n"
        f"- Localisation : {vehicle.get('location')}\n\n"
        f"Règles :\n"
        f"- Texte vendeur\n"
        f"- Clair\n"
        f"- Aucun mensonge\n"
    )

    if max_chars:
        base += f"- Maximum {max_chars} caractères\n"

    return base


# -------------------------
# PROMPTS
# -------------------------

DG_SYSTEM_PROMPTS = {
    "truck": (
        "Tu es Daniel Giroux, vendeur automobile expérimenté à Saint-Georges (Beauce).\n"
        "Ton style est direct, confiant, vendeur mais crédible.\n"
        "Tu écris pour Facebook Marketplace.\n"
        "Pas d'exagération, pas d'invention, pas de jargon inutile.\n"
        "Accent sur la robustesse, l'utilité, la valeur réelle."
    ),
    "suv": (
        "Tu es Daniel Giroux, vendeur automobile.\n"
        "Style rassurant, pratique, orienté famille et polyvalence.\n"
        "Clair, structuré, facile à lire sur mobile."
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
        "Optimisé pour Facebook Marketplace."
    ),
}
