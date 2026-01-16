import os, re, tempfile, subprocess, sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="kenbot-text-engine", version="1.0")

class Job(BaseModel):
    slug: str
    event: str = "NEW"
    vehicle: Dict[str, Any]

def _clip_800(txt: str) -> str:
    t = (txt or "").strip()
    if len(t) <= 800:
        return t + "\n"
    return t[:800].rstrip() + "…\n"

def _looks_like_vin(v: str) -> bool:
    v = (v or "").strip().upper()
    return bool(re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", v))

@app.post("/generate")
def generate(job: Job):
    v = job.vehicle or {}
    title = (v.get("title") or "").strip()
    price = (v.get("price") or "").strip()
    mileage = (v.get("mileage") or "").strip()
    stock = (v.get("stock") or "").strip().upper()
    vin = (v.get("vin") or "").strip().upper()

    if not title:
        raise HTTPException(400, "vehicle.title manquant")

    # --- Si VIN valide -> on tente sticker_to_ad ---
    if _looks_like_vin(vin) and price and mileage and stock:
        pdf_url = f"https://www.chrysler.com/hostd/windowsticker/getWindowStickerPdf.do?vin={vin}"

        with tempfile.TemporaryDirectory(prefix="kb_sticker_") as td:
            td = Path(td)
            pdf_path = td / f"{vin}.pdf"

            # download PDF
            import requests
            r = requests.get(pdf_url, timeout=60)
            if r.ok and (r.content.startswith(b"%PDF")) and len(r.content) > 60_000:
                pdf_path.write_bytes(r.content)

                # call engine/sticker_to_ad.py (CLI)
                script = Path(__file__).resolve().parent / "engine" / "sticker_to_ad.py"
                if not script.exists():
                    raise HTTPException(500, f"sticker_to_ad.py introuvable: {script}")

                out_dir = td  # dossier tmp
                expected = out_dir / f"{stock}_facebook.txt"

                cmd = [
                    sys.executable, str(script), str(pdf_path),
                    "--out", str(out_dir),
                    "--title", title,
                    "--price", price,
                    "--mileage", mileage,
                    "--stock", stock,
                    "--vin", vin,
                ]
                p = subprocess.run(cmd, capture_output=True, text=True)

                if p.returncode != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"sticker_to_ad failed (code={p.returncode})\n"
                            f"STDERR:\n{(p.stderr or '')[-1200:]}\n"
                            f"STDOUT:\n{(p.stdout or '')[-1200:]}"
                        ),
                    )

                if not expected.exists():
                    raise HTTPException(500, f"sticker_to_ad OK mais fichier manquant: {expected}")

                full = expected.read_text(encoding="utf-8", errors="ignore")
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
