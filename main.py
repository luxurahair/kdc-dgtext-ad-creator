import os
import re
import sys
import tempfile
import subprocess
import traceback
from pathlib import Path
from typing import Any, Dict

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
    """Garde pour plus tard (Marketplace). NE PAS utiliser pour Facebook."""
    t = (txt or "").strip()
    if len(t) <= 800:
        return t + "\n"
    return t[:800].rstrip() + "…\n"


def _looks_like_vin(v: str) -> bool:
    v = (v or "").strip().upper()
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v))


# ==========================
# Supabase (DB + Storage)
# ==========================
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

STICKER_BUCKET = os.getenv("SB_BUCKET_STICKERS", "kennebec-stickers").strip()
OUTPUTS_BUCKET = os.getenv("SB_BUCKET_OUTPUTS", "kennebec-outputs").strip()

_sb = None


def sb():
    global _sb
    if _sb is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase env missing: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
        _sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _sb


# ==========================
# Sticker helpers
# ==========================
def _sticker_obj_path(vin: str) -> str:
    return f"pdf_ok/{vin.upper()}.pdf"


def is_pdf_ok(b: bytes) -> bool:
    # Règle officielle: <10KB = mauvais, et doit commencer par %PDF
    return bool(b) and len(b) >= 10_240 and b[:4] == b"%PDF"


def has_sticker_cached(vin: str) -> bool:
    """
    True si un PDF validé existe déjà dans Supabase Storage.
    Ne télécharge rien, ne fait aucun appel Chrysler.
    """
    vin = (vin or "").strip().upper()
    if not _looks_like_vin(vin):
        return False
    obj_path = _sticker_obj_path(vin)
    try:
        data = sb().storage.from_(STICKER_BUCKET).download(obj_path)
        return is_pdf_ok(data)
    except Exception:
        return False


def get_or_fetch_sticker_pdf(vin: str) -> Path:
    """
    Cache-only: retourne un PDF local (tmp) UNIQUEMENT depuis Supabase Storage.
    Aucun appel Chrysler / aucun lookup ici.
    """
    vin = (vin or "").strip().upper()
    if not _looks_like_vin(vin):
        raise RuntimeError("VIN invalide")

    obj_path = _sticker_obj_path(vin)
    tmp_dir = Path(tempfile.mkdtemp(prefix="kb_pdf_"))
    local_pdf = tmp_dir / Path(obj_path).name

    try:
        data = sb().storage.from_(STICKER_BUCKET).download(obj_path)
    except Exception:
        raise RuntimeError("Sticker absent du cache Supabase")

    if not is_pdf_ok(data):
        raise RuntimeError("Sticker présent mais invalide")

    local_pdf.write_bytes(data)
    return local_pdf


# ==========================
# Outputs (Storage + DB)
# ==========================
def outputs_put(path: str, content: str) -> None:
    sb().storage.from_(OUTPUTS_BUCKET).upload(
        path,
        content.encode("utf-8"),
        {"content-type": "text/plain; charset=utf-8", "upsert": "true"},
    )


def outputs_upsert(stock: str, kind: str, fb_path: str, mp_path: str) -> None:
    sb().table("outputs").upsert(
        {
            "stock": stock,
            "kind": kind,
            "facebook_path": fb_path,
            "marketplace_path": mp_path,
        }
    ).execute()


def outputs_remove(path: str) -> None:
    try:
        sb().storage.from_(OUTPUTS_BUCKET).remove([path])
    except Exception:
        pass


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
        "outputs_bucket": OUTPUTS_BUCKET,
        "has_supabase": bool(SUPABASE_URL and SUPABASE_KEY),
        "build": "tryexcept-2026-01-18-1",
    }


@app.post("/generate")
def generate(job: Job):
    try:
        v = job.vehicle or {}
        title = (v.get("title") or "").strip()
        price = (v.get("price") or "").strip()
        mileage = (v.get("mileage") or "").strip()
        stock = (v.get("stock") or "").strip().upper() or job.slug.strip().upper()
        vin = (v.get("vin") or "").strip().upper()

        if not title:
            raise HTTPException(400, "vehicle.title manquant")

        # ==========================
        # WITH (sticker_to_ad) - cache-only
        # ==========================
        pdf_path = None
        if _looks_like_vin(vin) and price and mileage and stock:
            try:
                pdf_path = get_or_fetch_sticker_pdf(vin)
                print(f"WITH_OK vin={vin} path=pdf_ok/{vin}.pdf stock={stock}")
            except Exception as e:
                print(f"WITH_SKIP vin={vin} path=pdf_ok/{vin}.pdf stock={stock} err={e}")
                pdf_path = None
        else:
            print(f"WITH_SKIP vin={vin} stock={stock} (vin invalide ou price/mileage/stock manquant)")

        if pdf_path:
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

                candidates = sorted(
                    out_dir.glob("*_facebook.txt"),
                    key=lambda x: x.stat().st_mtime,
                    reverse=True,
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

                full = candidates[0].read_text(encoding="utf-8", errors="ignore")
                return {"slug": job.slug, "facebook_text": full}
        # ==========================
        # WITHOUT (fallback)
        # ==========================
        base = f"🔥 {title} 🔥\n\n"
        if price:
            base += f"💥 {price} 💥\n"
        if mileage:
            base += f"📊 {mileage}\n"
        if stock:
            base += f"🧾 Stock : {stock}\n"

        # Pas de lien Chrysler. On mentionne seulement si déjà en cache.
        if has_sticker_cached(vin):
            base += "🧾 Window Sticker : disponible sur demande\n"

        # archive outputs (WITHOUT)
        fb_path = f"without/{stock}_facebook.txt"
        mp_path = f"without/{stock}_marketplace.txt"
        outputs_put(fb_path, base)
        outputs_put(mp_path, base)
        outputs_upsert(stock, "without", fb_path, mp_path)

        return {"slug": job.slug, "facebook_text": base}

    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=tb[-2000:])

