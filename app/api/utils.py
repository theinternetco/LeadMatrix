import os
from datetime import datetime

def generate_csv_path(api_key: str) -> str:
    filename = f"leads_export_{api_key}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    path = os.path.join("/tmp", filename)
    return path
