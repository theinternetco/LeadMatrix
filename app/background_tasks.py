import csv

def export_to_csv_task(leads, filepath: str):
    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["name", "phone", "address", "lat", "lng", "source"])
        for lead in leads:
            writer.writerow([lead.name, lead.phone, lead.address, lead.lat, lead.lng, lead.source])