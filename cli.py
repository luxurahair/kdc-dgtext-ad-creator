import argparse, json
from pathlib import Path

def build_texts(vehicle: dict) -> tuple[str, str]:
    title = (vehicle.get("title") or "").strip()
    price = vehicle.get("price", "")
    km = vehicle.get("km", "")
    stock = (vehicle.get("stock") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    loc = (vehicle.get("location") or "").strip()

    marketplace = (
        f"🔥 {title} 🔥\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n"
        f"📩 Écris-moi en privé"
    )

    # Marketplace safe limit (<800). On garde marge.
    if len(marketplace) > 790:
        marketplace = marketplace[:790].rsplit("\n", 1)[0]

    facebook = (
        f"🔥 {title} 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n\n"
        f"📩 Daniel Giroux — je réponds vite."
    )
    return facebook, marketplace

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

    print("✅ Wrote:", out / "facebook_dg.txt")
    print("✅ Wrote:", out / "marketplace.txt")

if __name__ == "__main__":
    main()
