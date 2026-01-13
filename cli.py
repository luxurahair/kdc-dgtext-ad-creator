# cli.py
import argparse
import json
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from engine.classifier import classify

def build_fallback(vehicle: dict, kind: str) -> tuple[str, str]:
    from profiles import exotic, truck, suv, default
    if kind == "exotic":
        return exotic.build(vehicle)
    if kind == "truck":
        return truck.build(vehicle)
    if kind == "suv":
        return suv.build(vehicle)
    return default.build(vehicle)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="outdir", required=True)

    # ✅ NOUVEAU: IA uniquement si demandé
    ap.add_argument("--ai", action="store_true", help="Generate optional AI versions (requires OPENAI_API_KEY)")
    args = ap.parse_args()

    vehicle = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    kind = classify(vehicle)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # ✅ Base déterministe toujours
    fb, mp = build_fallback(vehicle, kind)
    (out / "facebook_dg.txt").write_text(fb, encoding="utf-8")
    (out / "marketplace.txt").write_text(mp, encoding="utf-8")

    # ✅ Optionnel: versions AI EN PLUS (ne remplacent jamais)
    if args.ai:
        if not os.getenv("OPENAI_API_KEY"):
            raise SystemExit("OPENAI_API_KEY missing but --ai was requested.")
        from engine.llm import generate_ad_text
        fb_ai = generate_ad_text(vehicle, kind)
        mp_ai = generate_ad_text(vehicle, kind, max_chars=800)
        (out / "facebook_ai.txt").write_text(fb_ai, encoding="utf-8")
        (out / "marketplace_ai.txt").write_text(mp_ai, encoding="utf-8")

    print("✅ profile:", kind)
    print("✅ Wrote:", out / "facebook_dg.txt")
    print("✅ Wrote:", out / "marketplace.txt")
    if args.ai:
        print("✅ Wrote:", out / "facebook_ai.txt")
        print("✅ Wrote:", out / "marketplace_ai.txt")

if __name__ == "__main__":
    main()
