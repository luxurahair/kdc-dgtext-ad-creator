import os
import re
import sys
import tempfile
import subprocess
import traceback
from pathlib import Path
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from supabase import create_client

app = FastAPI(title="kenbot-text-engine", version="1.0")


# ==========================
# Models
# ==========================
class Job(BaseModel):
    slug: str
    event: str = "NEW"
    vehicle: Dict[str, Any]


# ==========================
# Helpers
# ==========================
def _clip_800(txt: str) -> str:
    t = (txt or "").strip()
    if len(t) <= 800:
        return t + "\n"
    return t[:800].rstrip() + "…\n"


def _looks_like_vin(v: str) -> bool:
    v = (v or "").strip().upper()
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v))


# ==========================
# Supabase Storage (PDF cache)
# ==========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
STICKER_BUCKET = os.getenv("SUPABASE_STICKER_BUCKET", "window-stickers").strip()

_sb = None


def sb():
    global _sb
    if _sb is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase env missing: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
        _sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _sb


def _sticker_obj_path(vin: str) -> str:
    return f"{vin.upper()}.pdf"


def get_or_fetch_sticker_pdf(vin: str) -> Path:
    """
    Retourne un PDF local (tmp) en:
    1) essayant Supabase Storage (bucket window-stickers)
    2) sinon télécharge Chrysler et upload en cache
    """
    vin = (vin or "").strip().upper()
    if not _looks_like_vin(vin):
        raise RuntimeError("VIN invalide")

    obj_path = _sticker_obj_path(vin)
    tmp_dir = Path(tempfile.mkdtemp(prefix="kb_pdf_"))
    local_pdf = tmp_dir / obj_path

    # 1) download depuis Supabase Storage
    try:
        data = sb().storage.from_(STICKER_BUCKET).download(obj_path)
        if data and len(data) > 60_000 and data[:4] == b"%PDF":
            local_pdf.write_bytes(data)
            return local_pdf
    except Exception:
        pass

    # 2) download Chrysler
    pdf_url = f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"
    r = requests.get(pdf_url, timeout=60)
    if not (r.ok and r.content.startswith(b"%PDF") and len(r.content) > 60_000):
        raise RuntimeError("Sticker Chrysler non récupéré ou PDF invalide")

    local_pdf.write_bytes(r.content)

    # 3) upload Supabase Storage (cache durable)
    try:
        sb().storage.from_(STICKER_BUCKET).upload(
            obj_path,
            r.content,
            {"content-type": "application/pdf", "upsert": "true"},
        )
    except Exception:
        # pas bloquant: on a déjà le PDF local
        pass

    return local_pdf


# ==========================
# Routes
# ==========================
@app.get("/health")
def health():
    return {"ok": True}


@app.get("/version")
def version():
    return {
        "has_sticker_to_ad": True,
        "debug_traceback": True,
        "sticker_bucket": STICKER_BUCKET,
        "has_supabase": bool(SUPABASE_URL and SUPABASE_KEY),
    }


@app.post("/generate")
def generate(job: Job):
    try:
        v = job.vehicle or {}
        title = (v.get("title") or "").strip()
        price = (v.get("price") or "").strip()
        mileage = (v.get("mileage") or "").strip()
        stock = (v.get("stock") or "").strip().upper()
        vin = (v.get("vin") or "").strip().upper()

        if not title:
            raise HTTPException(400, "vehicle.title manquant")

        # --- VIN valide -> PDF cache -> sticker_to_ad ---
        if _looks_like_vin(vin) and price and mileage and stock:
            pdf_path = get_or_fetch_sticker_pdf(vin)

            with tempfile.TemporaryDirectory(prefix="kb_sticker_") as td:
                out_dir = Path(td)

                script = Path(__file__).resolve().parent / "engine" / "sticker_to_ad.py"
                if not script.exists():
                    raise HTTPException(500, f"sticker_to_ad.py introuvable: {script}")

                cmd = [
                    sys.executable, str(script), str(pdf_path),
                    "--out", str(out_dir),
                    "--title", title,
                    "--price", price,
                    "--mileage", mileage,
                    "--stock", stock,
                    "--vin", vin,
                ]

                try:
                    p = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
                except subprocess.TimeoutExpired:
                    raise HTTPException(500, "sticker_to_ad timeout (25s)")

                if p.returncode != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"sticker_to_ad failed (code={p.returncode})\n"
                            f"STDERR:\n{(p.stderr or '')[-1200:]}\n"
                            f"STDOUT:\n{(p.stdout or '')[-1200:]}"
                        ),
                    )

                # prendre le *_facebook.txt le plus récent
                candidates = sorted(
                    out_dir.glob("*_facebook.txt"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True
                )

                if not candidates:
                    generated = [x.name for x in out_dir.glob("*")]
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            "sticker_to_ad: aucun *_facebook.txt généré\n"
                            f"generated={generated}\n"
                            f"STDERR:\n{(p.stderr or '')[-800:]}\n"
                            f"STDOUT:\n{(p.stdout or '')[-800:]}"
                        ),
                    )

                best = candidates[0]
                full = best.read_text(encoding="utf-8", errors="ignore")
                return {"slug": job.slug, "facebook_text": _clip_800(full)}

        # --- Fallback: texte court (sans options) ---
        base = f"🔥 {title} 🔥\n\n"
        if price:
            base += f"💥 {price} 💥\n"
        if mileage:
            base += f"📊 {mileage}\n"
        if stock:
            base += f"🧾 Stock : {stock}\n"
        if _looks_like_vin(vin):
            base += f"🧾 Window Sticker : https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}\n"

        return {"slug": job.slug, "facebook_text": _clip_800(base)}

    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=tb[-2000:])
