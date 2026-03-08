# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

def is_allowed_stellantis_brand(txt: str) -> bool:
    low = (txt or "").lower()
    allowed = (
        "ram", "dodge", "jeep", "chrysler",
        "alfa", "alfaromeo", "alfa romeo",
        "fiat", "wagoneer"
    )
    return any(a in low for a in allowed)

# --------------------------
# Helpers (pure, no I/O)
# --------------------------
def _s(x: Any) -> str:
    return ("" if x is None else str(x)).strip()

def normalize_whitespace(text: str) -> str:
    t = (text or "").replace("\xa0", " ")
    t = " ".join(t.split())
    return t.strip()

def _uniq_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for x in items or []:
        s = normalize_whitespace(str(x))
        if not s:
            continue
        k = s.casefold()
        if k in seen:
            continue
        seen.add(k)
        out.append(s)
    return out

def _clean_bullet_line(s: str) -> str:
    s = normalize_whitespace(s)
    s = s.lstrip("■•-–— ").strip()
    return s

def _is_stellantis(vehicle: Dict[str, Any]) -> bool:
    title = _s(vehicle.get("title"))
    make = _s(vehicle.get("make")).lower()
    if make in ("ram", "jeep", "dodge", "chrysler", "fiat", "wagoneer", "alfaromeo", "alfa romeo", "alfa"):
        return True
    return bool(title and is_allowed_stellantis_brand(title))

def _format_headline(headline: str) -> str:
    h = normalize_whitespace(headline)
    if not h:
        return ""
    h = h.replace("*", "").strip(" •")
    return f"*{h}*"

def _format_specs_lines(specs: Dict[str, str]) -> List[str]:
    specs = specs or {}
    def g(*keys: str) -> str:
        for k in keys:
            v = specs.get(k)
            if v:
                return normalize_whitespace(v)
        return ""
    out: List[str] = []
    tr = g("transmission")
    cy = g("cylindres")
    dr = g("entrainement", "entra\u00eenement")
    fu = g("carburant")
    ps = g("passagers")
    ex = g("couleur ext.")
    ins = g("couleur int.")
    mpg = g("mpg", "consommation")  # Ajout moderne : MPG si dispo
    if tr: out.append(f"• Transmission : {tr}")
    if cy: out.append(f"• Cylindres : {cy}")
    if dr: out.append(f"• Entraînement : {dr}")
    if fu: out.append(f"• Carburant : {fu}")
    if mpg: out.append(f"• Consommation : {mpg}")
    if ps: out.append(f"• Passagers : {ps}")
    if ex: out.append(f"• Couleur ext. : {ex}")
    if ins: out.append(f"• Couleur int. : {ins}")
    return out

def _hashtags_for_vehicle(v: Dict[str, Any]) -> str:
    make = _s(v.get("make")).lower()
    title = _s(v.get("title")).lower()
    base = [
        "#VehiculeOccasion", "#AutoUsagée", "#Quebec", "#Beauce",
        "#SaintGeorges", "#KennebecDodge", "#DanielGiroux"
    ]
    key = make or title
    if "jeep" in key:
        tags = ["#Jeep", "#Wrangler", "#4x4"] + base
    elif "ram" in key:
        tags = ["#RAM", "#Truck", "#Pickup"] + base
    elif "dodge" in key:
        tags = ["#Dodge"] + base
    elif "chrysler" in key:
        tags = ["#Chrysler"] + base
    elif "fiat" in key:
        tags = ["#Fiat"] + base
    elif "nissan" in key:
        tags = ["#Nissan", "#Rogue", "#VUS"] + base  # Ajout moderne par marque
    elif make:
        tags = [f"#{make.capitalize()}"] + base
    else:
        tags = base
    seen = set()
    out: List[str] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return " ".join(out)

def _choose_equipment_lines(vehicle: Dict[str, Any], sticker_lines: Optional[List[str]]) -> tuple[List[str], str]:
    """
    Priorité:
    1) sticker_lines (sticker_to_ad) si non vide
    2) comfort (max 8)
    3) features (max 8)
    4) Nouveau : templates génériques par marque si vide
    """
    sticker_lines = sticker_lines or []
    st = [normalize_whitespace(x) for x in sticker_lines if normalize_whitespace(x)]
    if st:
        return st, "Window Sticker"

    comfort = vehicle.get("comfort") or []
    if isinstance(comfort, list) and comfort:
        c = _uniq_keep_order([normalize_whitespace(str(x)) for x in comfort])[:8]
        if c:
            return c, "Kennebec"

    feats = vehicle.get("features") or []
    if isinstance(feats, list) and feats:
        f = _uniq_keep_order([normalize_whitespace(str(x)) for x in feats])[:8]
        if f:
            return f, "Kennebec"

    # Nouveau : Templates génériques (modernisation)
    GENERIC_TEMPLATES = {
        'nissan': [
            '■ Système AWD intelligent pour routes Beauce',
            '■ Caméra 360° pour manœuvres faciles',
            '■ Sièges chauffants (idéal hiver québécois)',
            '■ Apple CarPlay / Android Auto',
            '■ Écran tactile 8-9 pouces',
        ],
        'toyota': [
            '■ Fiabilité légendaire Toyota',
            '■ Économie essence supérieure',
            '■ Sécurité Toyota Safety Sense',
            '■ Sièges confortables pour longs trajets',
        ],
        'honda': [
            '■ Moteur performant et économe',
            '■ Système Honda Sensing',
            '■ Intérieur spacieux',
            '■ Apple CarPlay / Android Auto',
        ],
        # Ajoute d'autres marques au besoin
        'default': [
            '■ Options confort standard',
            '■ Inspecté et garanti',
            '■ Prêt pour la route',
        ],
    }
    low_title = (vehicle.get('title') or '').lower()
    for brand, tmpl in GENERIC_TEMPLATES.items():
        if brand in low_title:
            return tmpl, "Générique"
    return GENERIC_TEMPLATES['default'], "Générique"

# --------------------------
# Text builders (DG long vendeur, modernisé)
# --------------------------
def build_facebook_dg(vehicle: Dict[str, Any], sticker_lines: Optional[List[str]] = None) -> str:
    """
    Facebook = VERSION LONGUE DG (vendeur), modernisée avec AI blend optionnel.
    """
    title = _s(vehicle.get("title"))
    price = _s(vehicle.get("price"))
    mileage = _s(vehicle.get("mileage") or vehicle.get("km"))
    stock = _s(vehicle.get("stock")).upper()
    url = _s(vehicle.get("url"))
    vin = _s(vehicle.get("vin")).upper()
    headline = _s(vehicle.get("headline_features"))
    specs = vehicle.get("specs") or {}
    year = _s(vehicle.get("year"))
    transmission = _s(vehicle.get("transmission"))
    fuel = _s(vehicle.get("fuel"))
    drivetrain = _s(vehicle.get("drivetrain"))
    body = _s(vehicle.get("body"))
    stellantis = _is_stellantis(vehicle)
    if not stellantis:
        vin = ""

    lines: List[str] = []

    # Nouveau : Option AI intro (si env key)
    if os.getenv("OPENAI_API_KEY"):
        try:
            from llm import generate_ad_text  # Assume dans engine
            from classifier import classify
            kind = classify(vehicle)
            ai_intro = generate_ad_text(vehicle, kind, max_chars=200)  # Intro naturelle
            lines.append(ai_intro)
            lines.append("")
        except ImportError:
            if os.getenv("DEBUG") == "1":
                print("AI import fail - fallback DG")

    lines.append(f"🔥 {title} 🔥")
    lines.append("")

    hl = _format_headline(headline)
    if hl:
        lines.append(hl)
        lines.append("")

    if price:
        lines.append(f"💥 {price} 💥")
    if mileage:
        lines.append(f"📊 Kilométrage : {mileage}")

    lines.append("📍 Kennebec Dodge Chrysler — Saint-Georges (Beauce)")
    lines.append("")

    lines.append("🚗 DÉTAILS")
    if stock:
        lines.append(f"✅ Inventaire : {stock}")
    if year:
        lines.append(f"✅ Année : {year}")
    if vin:
        lines.append(f"✅ VIN : {vin}")
    if transmission:
        lines.append(f"✅ Transmission : {transmission}")
    if drivetrain:
        lines.append(f"✅ Entraînement : {drivetrain}")
    if fuel:
        lines.append(f"✅ Carburant : {fuel}")
    if body:
        lines.append(f"✅ Carrosserie : {body}")

    lines.append("📄 Vente commerciale — 2 taxes applicables")
    lines.append("✅ Inspection complète — véhicule propre & prêt à partir.")
    lines.append("")

    equipment_lines, source_label = _choose_equipment_lines(vehicle, sticker_lines)
    if equipment_lines:
        if source_label == "Window Sticker":
            lines.append("✨ ACCESSOIRES OPTIONNELS (Window Sticker)")
        elif source_label == "Générique":
            lines.append("✨ ÉQUIPEMENTS TYPIQUES (à confirmer)")
        else:
            lines.append("✨ ÉQUIPEMENTS & CONFORT — CE QUI FAIT LA DIFFÉRENCE")
        if source_label == "Window Sticker" and any(x.startswith("✅") or "▫️" in x for x in equipment_lines):
            for it in equipment_lines:
                s = normalize_whitespace(it)
                if s:
                    lines.append(s)
        else:
            for it in equipment_lines[:10]:
                t = _clean_bullet_line(it)
                if t:
                    lines.append(f"■ {t}")
        lines.append("")

    if url:
        lines.append("🔗 Fiche complète :")
        lines.append(url)
        lines.append("")

    if vin and stellantis:
        lines.append("🧾 Window Sticker :")
        lines.append(f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}")
        lines.append("")

    # Footer DG long, modernisé avec localisation
    lines.append("🔁 J’accepte les échanges : 🚗 auto • 🏍️ moto • 🛥️ bateau • 🛻 VTT • 🏁 côte-à-côte")
    lines.append("📸 Envoie-moi les photos + infos de ton échange (année / km / paiement restant) → je te reviens vite.")
    lines.append("")
    lines.append("👋 Publiée par Daniel Giroux — je réponds vite (pas un robot, promis 😄)")
    lines.append("📍 Saint-Georges (Beauce) | Prise de possession rapide possible")
    lines.append("📄 Vente commerciale — 2 taxes applicables")
    lines.append("✅ Inspection complète — véhicule propre & prêt à partir.")
    lines.append("")
    lines.append("📩 Écris-moi en privé — ou texte direct")
    lines.append("📞 Daniel Giroux — 418-222-3939")
    lines.append("")
    lines.append(_hashtags_for_vehicle(vehicle))

    return "\n".join(lines).strip() + "\n"

def build_marketplace_dg(vehicle: Dict[str, Any], sticker_lines: Optional[List[str]] = None) -> str:
    """
    Marketplace = VERSION COMPACTE (pas 40 lignes de blabla), modernisée.
    Limite ~800 chars.
    """
    title = _s(vehicle.get("title"))
    price = _s(vehicle.get("price"))
    mileage = _s(vehicle.get("mileage") or vehicle.get("km"))
    stock = _s(vehicle.get("stock")).upper()
    url = _s(vehicle.get("url"))
    vin = _s(vehicle.get("vin")).upper()
    stellantis = _is_stellantis(vehicle)
    if not stellantis:
        vin = ""

    lines: List[str] = []

    # AI compact si key
    if os.getenv("OPENAI_API_KEY"):
        try:
            from llm import generate_ad_text
            from classifier import classify
            kind = classify(vehicle)
            ai_compact = generate_ad_text(vehicle, kind, max_chars=400)
            lines.append(ai_compact)
            lines.append("")
        except ImportError:
            pass

    lines.append(f"🔥 {title} 🔥")
    if price:
        lines.append(f"💥 {price} 💥")
    if mileage:
        lines.append(f"📊 {mileage}")
    if stock:
        lines.append(f"📦 Inventaire : {stock}")

    lines.append("📄 Vente commerciale — 2 taxes applicables")
    lines.append("✅ Inspection complète — prêt à partir")
    lines.append("")

    equipment_lines, source_label = _choose_equipment_lines(vehicle, sticker_lines)
    if equipment_lines:
        lines.append("✨ Options (Window Sticker) :" if source_label == "Window Sticker" else "✨ Options & confort :")
        if source_label == "Window Sticker" and any(x.startswith("✅") for x in equipment_lines):
            picks = [normalize_whitespace(x).replace("✅", "■").strip() for x in equipment_lines if x.startswith("✅")]
            for it in picks[:10]:
                if it:
                    lines.append(it)
        else:
            for it in equipment_lines[:8]:
                t = _clean_bullet_line(it)
                if t:
                    lines.append(f"■ {t}")
        lines.append("")

    lines.append("📍 Kennebec Dodge Chrysler — Saint-Georges (Beauce)")
    lines.append("")

    if url:
        lines.append("🔗 Fiche complète :")
        lines.append(url)
        lines.append("")

    if vin and stellantis:
        lines.append("🧾 Window Sticker :")
        lines.append(f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}")
        lines.append("")

    lines.append("📞 Daniel Giroux — 418-222-3939")

    text = "\n".join(lines).strip() + "\n"
    # Compactage moderne : Clip si >800 chars
    if len(text) > 800:
        text = text[:800].rstrip() + "…\nPlus de détails en privé !"

    return text
