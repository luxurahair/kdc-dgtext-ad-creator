import argparse, json, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from engine.classifier import classify
from engine.llm import generate_ad_text
from profiles import exotic, truck, suv, default


def build_fallback(vehicle: dict, kind: str) -> tuple[str, str]:
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
    args = ap.parse_args()

    vehicle = json.loads(Path(args.inp).read_text(encoding="utf-8"))
    kind = classify(vehicle)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # 🔥 PRIORITÉ AU LLM
    if os.getenv("OPENAI_API_KEY"):
        fb = generate_ad_text(vehicle, kind)
        mp = generate_ad_text(vehicle, kind, max_chars=800)
    else:
        fb, mp = build_fallback(vehicle, kind)

    (out / "facebook_dg.txt").write_text(fb, encoding="utf-8")
    (out / "marketplace.txt").write_text(mp, encoding="utf-8")

    print("✅ profile:", kind)
    print("✅ Wrote:", out / "facebook_dg.txt")
    print("✅ Wrote:", out / "marketplace.txt")


if __name__ == "__main__":
    main()
