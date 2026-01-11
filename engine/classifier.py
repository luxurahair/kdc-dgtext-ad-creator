cat > engine/classifier.py <<'PY'
def classify(vehicle: dict) -> str:
    title = (vehicle.get("title") or "").lower()
    brand = (vehicle.get("brand") or "").lower()

    exotic_brands = ("ferrari", "lamborghini", "mclaren", "aston", "maserati", "bentley", "rolls", "porsche")
    if any(b in brand for b in exotic_brands) or any(b in title for b in exotic_brands):
        return "exotic"

    # SUV/VUS (mots-clés simples v1)
    suv_words = ("suv", "vus", "cherokee", "grand cherokee", "wrangler", "gladiator", "tahoe", "suburban", "explorer", "highlander", "rav4", "cr-v", "cx-5")
    if any(w in title for w in suv_words):
        return "suv"

    # Truck
    truck_brands = ("ram", "ford", "chevrolet", "gmc", "toyota", "nissan")
    truck_words = ("1500", "2500", "3500", "f-150", "f150", "silverado", "sierra", "tacoma", "tundra")
    if any(b in brand for b in truck_brands) and any(w in title for w in truck_words):
        return "truck"

    return "default"
PY
