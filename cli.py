cat > cli.py <<'PY'
import argparse, json
from pathlib import Path

from engine.classifier import classify
from profiles import exotic, truck, suv, default

def build_texts(vehicle: dict) -> tuple[str, str]:
    kind = classify(vehicle)
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
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    fb, mp = build_texts(vehicle)
    (out / "facebook_dg.txt").write_text(fb, encoding="utf-8")
    (out / "marketplace.txt").write_text(mp, encoding="utf-8")

    print("✅ profile:", classify(vehicle))
    print("✅ Wrote:", out / "facebook_dg.txt")
    print("✅ Wrote:", out / "marketplace.txt")

if __name__ == "__main__":
    main()
PY
