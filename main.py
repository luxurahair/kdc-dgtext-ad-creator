from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional

# Ton pipeline texte (à ajuster selon ton repo)
# 1) Si tu as engine/text_pipeline.py avec une fonction stable
try:
    from engine.text_pipeline import build_publish_text  # ou generate_facebook_text
except Exception:
    build_publish_text = None

app = FastAPI(title="kenbot-text-engine", version="1.0")

class Job(BaseModel):
    slug: str
    event: str = "NEW"
    vehicle: Dict[str, Any]

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/generate")
def generate(job: Job):
    if build_publish_text is None:
        raise HTTPException(
            status_code=500,
            detail="text_pipeline introuvable. Vérifie engine/text_pipeline.py et le nom de la fonction.",
        )

    try:
        # Ton pipeline attend probablement vehicle + (options/sticker_lines) selon ton code.
        # Ici on passe juste vehicle; adapte si ta fonction demande plus.
        text = build_publish_text(job.vehicle)  # <-- si signature différente, on ajuste
        text = (text or "").strip()
        if not text:
            raise ValueError("texte vide")
        return {"slug": job.slug, "facebook_text": text + "\n"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
