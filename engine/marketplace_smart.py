#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marketplace Smart — générateur d'annonces Marketplace punchées (≤ 800 caractères)
- Pensé pour les véhicules WITHOUT (pas de window sticker)
- Déterministe, clair, vendeur, sans chiffres/specs inventés.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re


# -----------------------------
# Normalisation / helpers
# -----------------------------

def _norm(s: str) -> str:
    s = (s or "").strip()
    s = s.replace("’", "'").replace("−", "-").replace("–", "-").replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s

def _shorten(s: str, limit: int) -> str:
    s = _norm(s)
    if len(s) <= limit:
        return s
    cut = s[:limit]
    for sep in ["\n", " • ", " | ", " - ", ". "]:
        i = cut.rfind(sep)
        if i >= int(limit * 0.6):
            return cut[:i].rstrip()
    return cut.rstrip()

def _fmt_money(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (int, float)):
        v = int(round(float(x)))
        s = f"{v:,}".replace(",", " ")
        return f"{s} $"
    s = str(x).strip()
    return "" if s.lower() in ("none", "null", "0", "0.0") else s

def _fmt_km(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (int, float)):
        v = int(round(float(x)))
        s = f"{v:,}".replace(",", " ")
        return f"{s} km"
    s = str(x).strip()
    return "" if s.lower() in ("none", "null", "0", "0.0") else s

def _first_word(title: str) -> str:
    t = _norm(title).split()
    return t[0] if t else ""

def _detect_brand(title: str) -> str:
    low = _norm(title).lower()
    brands = [
        "ferrari","lamborghini","mclaren","porsche","aston martin","maserati","bentley","rolls",
        "mercedes","bmw","audi","lexus","cadillac","tesla",
        "ram","dodge","jeep","chrysler","ford","chevrolet","gmc","toyota","honda","hyundai","kia","mazda","subaru","nissan","volkswagen","volvo"
    ]
    for b in brands:
        if b in low:
            return b.title()
    return _first_word(title).title()

def _classify(title: str, price: Optional[float] = None) -> str:
    low = _norm(title).lower()
    brand = _detect_brand(title).lower()

    # exotic / luxury (heuristique)
    if any(x in low for x in ["ferrari","lamborghini","mclaren","huracan","aventador","720s","gt3","gt2","911 turbo","f8","roma"]):
        return "exotic"
    if brand in ["bentley","rolls","aston martin","maserati"] or (price is not None and price >= 120000):
        return "luxury"
    if any(x in low for x in ["ram","f-150","f150","silverado","sierra","tundra","tacoma","super duty","2500","3500"]):
        return "truck"
    if any(x in low for x in ["suv","cherokee","grand cherokee","wrangler","4runner","highlander","pilot","tiguan","q5","x5"]):
        return "suv"
    if any(x in low for x in ["mustang","camaro","corvette","supra","type r","sti","gti","srt","rt","r/t","scat pack"]):
        return "sport"
    return "daily"


# -----------------------------
# Profils (messages + hashtags)
# -----------------------------

@dataclass
class Profile:
    category: str
    headline: str
    bullets: List[str]
    proof: str
    hashtags: List[str]

def get_profile(title: str, price_val: Optional[float] = None) -> Profile:
    brand = _detect_brand(title)
    cat = _classify(title, price=price_val)

    base_hashtags = ["#DanielGiroux", "#Beauce", "#SaintGeorges", "#Quebec"]

    # ❗ Aucun chiffre “générique” ici.
    if cat == "exotic":
        return Profile(
            category="exotic",
            headline=f"💎 {title} — Prestigieux & rare 💎",
            bullets=[
                "🎯 Prestige • performance • exclusivité",
                "✨ Présence et finition haut de gamme",
                "✅ Inspection complète — prêt à partir",
            ],
            proof="WITHOUT — texte basé sur infos disponibles, sans options inventées.",
            hashtags=[f"#{brand}", "#Exotique", "#Supercar", "#AutoDePrestige"] + base_hashtags,
        )

    if cat == "truck":
        return Profile(
            category="truck",
            headline=f"🔥 {title} — Prêt à travailler 🔥",
            bullets=[
                "💪 Solide, fiable, prêt à partir",
                "🧰 Parfait pour chantier / remorquage / famille",
                "✅ Inspection complète — prêt à partir",
            ],
            proof="WITHOUT — texte basé sur infos disponibles, sans options inventées.",
            hashtags=["#Truck", "#Pickup", "#Camion"] + base_hashtags,
        )

    if cat == "luxury":
        return Profile(
            category="luxury",
            headline=f"💎 {title} — Luxe & présence 💎",
            bullets=[
                "✨ Confort haut de gamme",
                "🎯 Image premium, conduite douce",
                "✅ Inspection complète — prêt à partir",
            ],
            proof="WITHOUT — clair et crédible, sans promesses inventées.",
            hashtags=["#Luxe", "#Premium", "#AutoDeLuxe"] + base_hashtags,
        )

    if cat == "sport":
        return Profile(
            category="sport",
            headline=f"⚡ {title} — Performance au quotidien ⚡",
            bullets=[
                "🔥 Look + sensations",
                "🎯 Tenue de route & plaisir",
                "✅ Inspection complète — prêt à partir",
            ],
            proof="WITHOUT — clair, net, vendeur.",
            hashtags=["#Sport", "#Performance", "#PassionAuto"] + base_hashtags,
        )

    # daily / suv fallback
    return Profile(
        category=cat,
        headline=f"🔥 {title} — Bon rapport qualité/prix 🔥",
        bullets=[
            "✅ Inspection complète — prêt à partir",
            "🚗 Idéal au quotidien",
        ],
        proof="WITHOUT — infos disponibles, rien d’inventé.",
        hashtags=["#Auto", "#VehiculeOccasion"] + base_hashtags,
    )


# -----------------------------
# Générateur principal
# -----------------------------

def generate_marketplace_text(
    vehicle: Dict[str, Any],
    char_limit: int = 800,
    include_hashtags: bool = True,
) -> str:
    title = _norm(str(vehicle.get("title") or "")).strip()
    if not title:
        return "Annonce indisponible (titre manquant).\n"

    price_val = vehicle.get("price") if isinstance(vehicle.get("price"), (int, float)) else None
    price = _fmt_money(vehicle.get("price"))
    km = _fmt_km(vehicle.get("km") or vehicle.get("mileage"))
    stock = _norm(str(vehicle.get("stock") or "")).upper()
    location = _norm(str(vehicle.get("location") or "")).strip()

    prof = get_profile(title, price_val=price_val)

    lines: List[str] = []
    lines.append(prof.headline)

    # ✅ Pas de placeholders : on affiche seulement si présent
    if price:
        lines.append(f"💰 Prix : {price}")
    if km:
        lines.append(f"📊 Km : {km}")
    if stock:
        lines.append(f"🧾 Stock : {stock}")

    lines.append("")  # respiration

    for b in prof.bullets:
        if _norm(b):
            lines.append(_norm(b))

    lines.append(prof.proof)

    # CTA DG
    lines.append("📩 Écris-moi en privé — réponse rapide.")
    if location:
        lines.append(f"📍 {location}")
    else:
        lines.append("📍 Saint-Georges (Beauce)")

    if include_hashtags and prof.hashtags:
        lines.append(" ".join(prof.hashtags))

    text = "\n".join(lines).strip()

    if len(text) > char_limit:
        text = _shorten(text, char_limit)

    return text + "\n"
