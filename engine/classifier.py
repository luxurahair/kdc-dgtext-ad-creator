def classify(vehicle: dict) -> str:
    title = (vehicle.get("title") or "").lower()
    brand = (vehicle.get("brand") or "").lower()

    exotic_brands = ("ferrari", "lamborghini", "mclaren", "porsche")
    if any(b in brand for b in exotic_brands):
        return "exotic"

    suv_words = ("suv", "cherokee", "grand cherokee", "durango", "explorer")
    if any(w in title for w in suv_words):
        return "suv"

    truck_brands = ("ram", "ford", "chevrolet", "gmc", "toyota", "nissan")
    truck_words = ("1500", "2500", "3500", "f-150", "f150", "silverado", "sierra", "tacoma", "tundra")
    if any(b in brand for b in truck_brands) and any(w in title for w in truck_words):
        return "truck"

    return "default"
