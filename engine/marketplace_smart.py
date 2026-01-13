#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Marketplace Smart — générateur d'annonces Marketplace punchées (≤ 800 caractères)
- Pensé pour les véhicules WITHOUT (pas de window sticker)
- Compatible avec les valeurs DG : clair, vendeur, pas d'invention d'options.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
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
    # coupe au dernier séparateur avant limit
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
        # format fr-CA simple avec espaces
        v = int(round(float(x)))
        s = f"{v:,}".replace(",", " ")
        return f"{s} $"
    s = str(x).strip()
    return s

def _fmt_km(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (int, float)):
        v = int(round(float(x)))
        s = f"{v:,}".replace(",", " ")
        return f"{s} km"
    s = str(x).strip()
    return s

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
    # exotic
    if any(x in low for x in ["ferrari","lamborghini","mclaren","488","huracan","aventador","720s","gt3","gt2","911 turbo","488 gtb","f8","roma"]):
        return "exotic"
    if brand in ["bentley","rolls","aston Martin".lower(),"maserati"] or (price is not None and price >= 120000):
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

def get_profile(title: str, year: Any = None) -> Profile:
    brand = _detect_brand(title)
    cat = _classify(title)

    # Par défaut : punch + crédible (pas d'options inventées)
    base_hashtags = ["#DanielGiroux", "#Beauce", "#SaintGeorges", "#Quebec"]

    if cat == "exotic" and "488" in _norm(title).lower() and "ferrari" in _norm(title).lower():
        # Specs "génériques" 488 GTB (pas un claim d'options)
        return Profile(
            category="exotic",
            headline=f"🔥 {brand} 488 GTB — Supercar d’exception 🔥",
            bullets=[
                "💥 V8 biturbo 3.9L",
                "⚡ ~661 hp | 0–100 km/h ~3.0 s",
                "🏎️ Boîte F1 double embrayage (7 rapports)",
                "🎯 Prestige • performance • exclusivité",
            ],
            proof="Sans Window Sticker (WITHOUT) — infos factuelles, rien d’inventé.",
            hashtags=["#Ferrari", "#Ferrari488", "#488GTB", "#Supercar", "#Exotique", "#V8Biturbo"] + base_hashtags,
        )

    if cat == "truck":
        return Profile(
            category="truck",
            headline=f"🔥 {title} — Prêt à travailler 🔥",
            bullets=[
                "💪 Solide, fiable, prêt à partir",
                "🧰 Parfait pour chantier / remorquage / famille",
                "✅ Inspection complète",
            ],
            proof="WITHOUT — texte basé sur données réelles (pas d’options inventées).",
            hashtags=["#Truck", "#Pickup", "#4x4", "#Camion"] + base_hashtags,
        )

    if cat == "luxury":
        return Profile(
            category="luxury",
            headline=f"💎 {title} — Luxe & présence 💎",
            bullets=[
                "✨ Confort haut de gamme",
                "🎯 Image premium, conduite douce",
                "✅ Inspection complète",
            ],
            proof="WITHOUT — infos réelles, pas de promesses floues.",
            hashtags=["#Luxe", "#AutoDeLuxe", "#Premium"] + base_hashtags,
        )

    if cat == "sport":
        return Profile(
            category="sport",
            headline=f"⚡ {title} — Performance au quotidien ⚡",
            bullets=[
                "🔥 Sensations + look",
                "🎯 Tenue de route & plaisir",
                "✅ Inspection complète",
            ],
            proof="WITHOUT — clair, net, vendeur.",
            hashtags=["#Sport", "#Performance", "#PassionAuto"] + base_hashtags,
        )

    # daily / suv fallback
    return Profile(
        category=cat,
        headline=f"🔥 {title} — Excellent rapport qualité/prix 🔥",
        bullets=[
            "✅ Inspection complète",
            "🚗 Prête à partir",
        ],
        proof="WITHOUT — infos réelles, rien d’inventé.",
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
    year = vehicle.get("year") or ""
    price = _fmt_money(vehicle.get("price"))
    km = _fmt_km(vehicle.get("km") or vehicle.get("mileage"))
    stock = _norm(str(vehicle.get("stock") or "")).upper()
    vin = _norm(str(vehicle.get("vin") or "")).upper()

    prof = get_profile(title, year=year)

    lines: List[str] = []
    # Headline
    lines.append(prof.headline)

    # Placeholders / infos clés (garder de la place)
    if price:
        lines.append(f"💰 Prix : {price}")
    else:
        lines.append("💰 Prix : ____ $")
    if km:
        lines.append(f"📊 Km : {km}")
    else:
        lines.append("📊 Km : ____ km")

    if stock:
        lines.append(f"🧾 Stock : {stock}")
    else:
        lines.append("🧾 Stock : ____")

    if vin:
        lines.append(f"🔢 VIN : {vin}")
    else:
        lines.append("🔢 VIN : _____________")

    lines.append("")  # respiration

    # Bullets punch (sans inventer d'options)
    for b in prof.bullets:
        lines.append(b)

    lines.append(prof.proof)

    # CTA DG
    lines.append("📩 Écris-moi en privé — réponse rapide.")
    lines.append("📍 Saint-Georges (Beauce)")

    if include_hashtags and prof.hashtags:
        # Marketplace coupe parfois les hashtags : on les met en 1 ligne
        tagline = " ".join(prof.hashtags)
        lines.append(tagline)

    text = "\n".join([l for l in lines if l is not None]).strip()
    # Enforce char limit
    if len(text) > char_limit:
        text = _shorten(text, char_limit)
    return text + "\n"
