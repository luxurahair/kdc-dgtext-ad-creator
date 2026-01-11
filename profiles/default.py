def build(vehicle: dict) -> tuple[str, str]:
    title = (vehicle.get("title") or "").strip()
    price = vehicle.get("price", "")
    km = vehicle.get("km", "")
    stock = (vehicle.get("stock") or "").strip()
    vin = (vehicle.get("vin") or "").strip()
    loc = (vehicle.get("location") or "").strip() or "Saint-Georges (Beauce)"

    mp = (
        f"🔥 {title} 🔥\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n"
        f"📩 Écris-moi en privé"
    )
    if len(mp) > 790:
        mp = mp[:790].rsplit("\n", 1)[0]

    fb = (
        f"🔥 {title} 🔥\n\n"
        f"💰 {price} $\n"
        f"📊 {km} km\n"
        f"🧾 Stock : {stock}\n"
        f"🔢 VIN : {vin}\n"
        f"📍 {loc}\n\n"
        f"📩 Daniel Giroux — je réponds vite."
    )

    return fb, mp
