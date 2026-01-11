def build(vehicle: dict) -> tuple[str, str]:
    title = (vehicle.get("title") or "").strip()
    price = vehicle.get("price", "")
    km = vehicle.get("km", "")
    stock = (vehicle.get("stock") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    loc = (vehicle.get("location") or "").strip() or "Saint-Georges (Beauce)"

    bullets = [
        "🚙 VUS spacieux • confortable",
        "🛡️ Sécurité & stabilité 4 saisons",
        "✅ Parfait famille & roadtrips"
    ]

    mp = (
        f"🔥 {title} — VUS PARFAIT 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n\n"
        + "\n".join(bullets) + "\n\n"
        f"📍 {loc}\n"
        f"📩 Écris-moi en privé — réponse rapide\n"
        f"#VUS #SUV #DanielGiroux #Beauce"
    ).strip()

    if len(mp) > 790:
        mp = mp[:790].rsplit("\n", 1)[0]

    fb = (
        f"🔥 {title} 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n\n"
        "VUS idéal pour le Québec : confort, sécurité, espace.\n"
        "📩 Daniel Giroux — je réponds vite."
    )
    return fb, mp
