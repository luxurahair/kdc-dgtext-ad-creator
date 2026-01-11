def build(vehicle: dict) -> tuple[str, str]:
    title = (vehicle.get("title") or "").strip()
    price = vehicle.get("price", "")
    km = vehicle.get("km", "")
    stock = (vehicle.get("stock") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    loc = (vehicle.get("location") or "").strip() or "Saint-Georges (Beauce)"

    # Facts généraux (pas des options inventées)
    bullets = [
        "💥 V8 biturbo 3.9L • ~661 hp",
        "⚡ 0–100 km/h ~3.0 s",
        "🏎️ Boîte F1 double embrayage",
        "🎯 Prestige • performance • exclusivité",
    ]

    mp = (
        f"🔥 {title} — VÉHICULE D’EXCEPTION 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n\n"
        + "\n".join(bullets) + "\n\n"
        f"📍 {loc}\n"
        f"📩 Écris-moi en privé — réponse rapide\n"
        f"#Ferrari #Supercar #Exotique #DanielGiroux #Beauce"
    )

    # Limite marketplace safe (<800)
    mp = mp.strip()
    if len(mp) > 790:
        mp = mp[:790].rsplit("\n", 1)[0]

    fb = (
        f"🔥 {title} 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n\n"
        "Supercar italienne reconnue mondialement — puissance, prestige et exclusivité.\n"
        "📩 Daniel Giroux — je réponds vite."
    )

    return fb, mp
