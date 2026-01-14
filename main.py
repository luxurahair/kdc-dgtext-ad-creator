from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict

app = FastAPI(title="kenbot-text-engine", version="1.0")


class Job(BaseModel):
    slug: str
    event: str = "NEW"
    vehicle: Dict[str, Any]


@app.get("/")
def root():
    return {"ok": True, "service": "kenbot-text-engine"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/generate")
def generate(job: Job):
    """
    MVP: retourne un texte simple.
    Ensuite on branche engine/text_pipeline.py.
    """
    v = job.vehicle or {}
    title = (v.get("title") or "").strip()
    price = (v.get("price") or "").strip()
    mileage = (v.get("mileage") or "").strip()

    if not title:
        raise HTTPException(status_code=400, detail="vehicle.title manquant")

    lines = [f"🔥 {title} 🔥", ""]
    if price:
        lines.append(f"💥 {price} 💥")
    if mileage:
        lines.append(f"📊 {mileage}")
    text = "\n".join(lines).strip() + "\n"

    return {"slug": job.slug, "facebook_text": text}
