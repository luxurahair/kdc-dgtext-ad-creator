def classify(vehicle: dict) -> str:
    title = (vehicle.get("title") or "").lower()
    brand = (vehicle.get("brand") or "").lower()

    # EXOTIC (simple v1, on élargira)
    exotic_brands = ("ferrari", "lamborghini", "mclaren", "aston", "maserati", "bentley", "rolls", "porsche")
    if any(b in brand for b in exotic_brands) or any(b in title for b in exotic_brands):
        return "exotic"

    # TRUCK (v1)
    truck_brands = ("ram", "ford", "chevrolet", "gmc", "toyota", "nissan")
    if any(b in brand for b in truck_brands) and ("1500" in title or "2500" in title or "3500" in title or "f-150" in title):
        return "truck"

    return "default"
