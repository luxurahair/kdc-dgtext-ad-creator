# classifier.py – version intelligente 2026 pour personnaliser AI/hashtags/tone
def classify(vehicle: dict) -> str:
    """
    Détecte le type de véhicule pour adapter l'AI intro, hashtags et ton vendeur.
    Priorité : brand > title > mots-clés.
    """
    title = (vehicle.get("title") or "").lower()
    brand = (vehicle.get("brand") or "").lower()
    model = (vehicle.get("model") or "").lower()
    full_text = f"{brand} {model} {title}".strip()

    # Exotic / haut de gamme (très recherchés, ton premium)
    exotic_brands = ("ferrari", "lamborghini", "mclaren", "porsche", "aston martin", "bentley", "rolls royce")
    if any(b in full_text for b in exotic_brands):
        return "exotic"

    # Truck / Pickup (robuste, travail, towing)
    truck_brands = ("ram", "ford", "chevrolet", "gmc", "toyota", "nissan")
    truck_words = ("1500", "2500", "3500", "f-150", "f150", "silverado", "sierra", "tacoma", "tundra", "pickup", "camion")
    if any(b in brand for b in truck_brands) and any(w in full_text for w in truck_words):
        return "truck"

    # SUV / CUV / VUS (familial, polyvalent, hiver Beauce)
    suv_words = ("suv", "cuv", "vus", "rogue", "cherokee", "grand cherokee", "durango", "explorer", "rav4", "cr-v", "highlander", "pilot", "pathfinder")
    if any(w in full_text for w in suv_words):
        return "suv"

    # Minivan / Familial (famille, sièges, espace)
    minivan_words = ("minivan", "caravan", "grand caravan", "pacifica", "odyssey", "sienna", "town & country")
    if any(w in full_text for w in minivan_words):
        return "minivan"

    # Sedan / Berline (économique, ville)
    sedan_words = ("sedan", "berline", "accord", "camry", "civic", "corolla", "malibu", "altima", "sentra")
    if any(w in full_text for w in sedan_words):
        return "sedan"

    # Coupe / Sport (performance, jeune)
    coupe_words = ("coupe", "charger", "challenger", "mustang", "camaro", "370z", "supra")
    if any(w in full_text for w in coupe_words):
        return "coupe"

    # EV / Hybride / Électrique (éco, futur, économie essence)
    ev_words = ("ev", "électrique", "hybrid", "hybride", "plug-in", "bolt", "leaf", "model 3", "ioniq", "prius")
    if any(w in full_text for w in ev_words):
        return "ev"

    # Default (catch-all)
    return "default"
