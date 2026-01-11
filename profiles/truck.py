def build(vehicle: dict) -> tuple[str, str]:
    title = (vehicle.get("title") or "").strip()
    price = vehicle.get("price", "")
    km = vehicle.get("km", "")
    stock = (vehicle.get("stock") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    loc = (vehicle.get("location") or "").strip() or "Saint-Georges (Beauce)"

    # Ici, on peut ajouter quelques arguments spécifiques aux camions
    bullets = [
        "🛻 Puissance et capacité de remorquage",
        "🔧 Marques de confiance (RAM, Ford, etc.)",
        "🚚 Conçu pour le travail et le loisir"
    ]

    mp = (
        f"🔥 {title} — CAMION ROBUSTE 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n\n"
        + "\n".join(bullets) + "\n\n"
        f"📍 {loc}\n"
        f"📩 Écris-moi en privé — réponse rapide\n"
        f"#Camion #Pickup #DanielGiroux #Beauce"
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
        "Un pickup conçu pour ceux qui ont besoin de puissance et de polyvalence.\n"
        "📩 Daniel Giroux — je réponds vite."
    )

    return fb, mp
