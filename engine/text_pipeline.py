# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Dépendances: build_ad + is_allowed_stellantis_brand doivent exister dans engine/ad_builder.py
from engine.ad_builder import build_ad, is_allowed_stellantis_brand

# pdfminer imports doivent être disponibles côté KenBot (requirements)
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTTextLine, LTChar


# --------------------------
# PDF helpers (bold detection)
# --------------------------

def _is_bold_font(fontname: str) -> bool:
    f = (fontname or "").lower()
    return any(x in f for x in ("bold", "black", "demi", "heavy", "semibold"))

def extract_lines_with_bold_from_pdf(pdf_path: Path) -> List[Tuple[str, bool]]:
    """
    Retourne [(ligne, is_bold)] basé sur la police.
    Marche seulement si le PDF contient du texte (pas juste une image).
    """
    out: List[Tuple[str, bool]] = []
    for page_layout in extract_pages(str(pdf_path)):
        for element in page_layout:
            if not isinstance(element, LTTextContainer):
                continue
            for line in element:
                if not isinstance(line, LTTextLine):
                    continue
                text = (line.get_text() or "").strip()
                if not text:
                    continue

                bold_chars = 0
                total_chars = 0
                for obj in line:
                    if isinstance(obj, LTChar):
                        total_chars += 1
                        if _is_bold_font(obj.fontname):
                            bold_chars += 1

                is_bold = (total_chars > 0 and (bold_chars / total_chars) >= 0.55)
                out.append((text, is_bold))
    return out


# --------------------------
# Text helpers
# --------------------------

def normalize_whitespace(text: str) -> str:
    t = (text or "").replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+\n", "\n", t)
    t = re.sub(r"\n\s+", "\n", t)
    return t.strip()

def stock_from_slug_or_name(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    s = s.split("/")[-1]
    s = s.replace("_facebook.txt", "").replace("_marketplace.txt", "")
    last = s.split("-")[-1].strip()
    return last.upper()

def strip_option_prices(lines: List[str]) -> List[str]:
    """
    Enlève les montants '$' à la fin/au début/entre parenthèses.
    """
    out: List[str] = []
    for x in (lines or []):
        s = (x or "").strip()
        s = re.sub(r"\s+\d[\d\s]*\s*\$\s*$", "", s)          # fin
        s = re.sub(r"^\$\s*\d[\d\s]*\s*", "", s)            # début
        s = re.sub(r"\(\s*\d[\d\s]*\s*\$\s*\)\s*$", "", s)  # (395 $)
        s = s.strip(" -•\t")
        if s:
            out.append(s)
    return out


# --------------------------
# sticker_lines -> options dict
# --------------------------

def parse_sticker_lines_to_options(lines: List[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    cur: Optional[Dict[str, Any]] = None

    def flush():
        nonlocal cur
        if cur and (cur.get("title") or "").strip():
            det = cur.get("details") or []
            uniq = []
            seen = set()
            for d in det:
                k = (d or "").strip().lower()
                if not k or k in seen:
                    continue
                seen.add(k)
                uniq.append(d.strip())
            cur["details"] = uniq[:12]
            out.append(cur)
        cur = None

    for raw in lines or []:
        s = (raw or "").strip()
        if not s:
            continue

        if s.startswith("✅"):
            flush()
            x = s.lstrip("✅").strip()
            title = x
            price = ""
            if "•" in x:
                left, right = x.split("•", 1)
                title = left.strip()
                price = right.strip()
            cur = {"title": title, "price": price, "details": []}
            continue

        if "▫️" in s:
            if cur is None:
                cur = {"title": "", "price": "", "details": []}
            sub = s.replace("_", "").replace("▫️", "").strip()
            if sub:
                cur["details"].append(sub)
            continue

    flush()
    return out[:40]


# --------------------------
# FB text (DG) — stable format
# --------------------------

def build_publish_text(vehicle: Dict[str, Any], sticker_lines: List[str]) -> str:
    """
    Texte DG (Facebook) en format build_ad().
    - options = sticker_lines (si Stellantis + sticker), sinon fallback comfort/features
    """
    title = (vehicle.get("title") or "").strip()
    price = (vehicle.get("price") or "").strip()
    mileage = (vehicle.get("mileage") or "").strip()
    stock = (vehicle.get("stock") or "").strip().upper()
    vin = (vehicle.get("vin") or "").strip().upper()
    url = (vehicle.get("url") or "").strip()

    options = parse_sticker_lines_to_options(sticker_lines or [])

    if not is_allowed_stellantis_brand(title):
        options = []
        vin = ""

    if not options:
        fallback = (vehicle.get("comfort") or vehicle.get("features") or [])[:12]
        options = [{"title": str(x).strip(), "price": "", "details": []} for x in fallback if str(x).strip()]

    return build_ad(
        title=title,
        price=price,
        mileage=mileage,
        stock=stock,
        vin=vin,
        options=options,
        vehicle_url=url,
    )


# --------------------------
# Marketplace text (A) — stable rules
# --------------------------

def build_marketplace_text(
    *,
    base_dir: Path,
    runtime_root: Path,
    slug: str,
    vehicle: Dict[str, Any],
    sticker_lines: List[str],
    sticker_pdf: Optional[Path] = None,
) -> str:
    """
    Marketplace = court + lisible.
    - Si sticker_pdf dispo : on passe par sticker_to_ad.py (format stable), puis on nettoie les prix
    - Sinon : fallback compact + points forts (strip prices)
    """
    title = (vehicle.get("title") or "").strip()
    price = (vehicle.get("price") or "").strip()
    mileage = (vehicle.get("mileage") or "").strip()
    stock = (vehicle.get("stock") or "").strip().upper()
    vin = (vehicle.get("vin") or "").strip().upper()
    url = (vehicle.get("url") or "").strip()

    if title and not is_allowed_stellantis_brand(title):
        vin = ""
        sticker_lines = []

    # 1) PDF dispo -> sticker_to_ad
    if sticker_pdf and Path(sticker_pdf).exists():
        script = (base_dir / "sticker_to_ad.py")
        if script.exists():
            out_dir = (runtime_root / "_tmp_marketplace_text")
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{slug}_marketplace_from_sticker.txt"

            py_venv = base_dir / ".venv" / "bin" / "python3"
            python_bin = str(py_venv) if py_venv.exists() else sys.executable

            r = subprocess.run(
                [
                    python_bin, str(script), str(sticker_pdf),
                    "--out", str(out_path),
                    "--title", title,
                    "--price", price,
                    "--mileage", mileage,
                    "--stock", stock,
                    "--vin", vin,
                    "--url", url,
                ],
                capture_output=True,
                text=True,
            )

            if r.returncode == 0 and out_path.exists():
                text = out_path.read_text(encoding="utf-8", errors="ignore").strip()

                fixed: List[str] = []
                for line in text.splitlines():
                    s = (line or "").rstrip()

                    # drop lignes "prix seulement"
                    if re.match(r"^\s*(✅|▫️|■|•)?\s*\d[\d\s]*\s*\$\b", s):
                        continue

                    s = re.sub(r"\s+\d[\d\s]*\s*\$\s*$", "", s)
                    s = re.sub(r"\(\s*\d[\d\s]*\s*\$\s*\)\s*$", "", s)
                    fixed.append(s)

                text = "\n".join([x for x in fixed if x.strip()]).strip()

                if vin and ("getWindowStickerPdf.do?vin=" not in text):
                    text += (
                        "\n\n📄 Window Sticker :\n"
                        f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"
                    )

                return text.strip() + "\n"

    # 2) fallback compact
    lines: List[str] = []
    if title:
        lines.append(f"🔥 {title} 🔥")
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
    if vin:
        lines.append(f"✅ VIN : {vin}")
    lines.append("")

    picks = strip_option_prices(sticker_lines or [])
    if not picks:
        fallback = (vehicle.get("comfort") or vehicle.get("features") or [])[:12]
        picks = [str(x).strip() for x in fallback if str(x).strip()]

    # Points forts (12 max)
    clean: List[str] = []
    for x in picks:
        s = (x or "").strip()
        s = s.replace("✅", "").replace("▫️", "").replace("■", "").replace("•", "").strip()
        if s:
            clean.append(s)

    uniq: List[str] = []
    seen = set()
    for s in clean:
        k = s.lower()
        if k in seen:
            continue
        seen.add(k)
        uniq.append(s)

    top = uniq[:12]
    if top:
        lines.append("⭐ Points forts : " + " | ".join(top))
        lines.append("")

    if vin:
        lines.append("📄 Window Sticker :")
        lines.append(f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}")
        lines.append("")

    if url:
        lines.append("🔗 Fiche complète :")
        lines.append(url)
        lines.append("")

    lines.append("📩 Écris-moi en privé — ou texte direct")
    return "\n".join(lines).strip() + "\n"
