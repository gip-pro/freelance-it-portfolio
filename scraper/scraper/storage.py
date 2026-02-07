import csv
import os
from typing import Dict

FIELDS = [
    "source",
    "listing_url",
    "date",
    "title",
    "price",
    "currency",
    "address",
    "address_status",
    "lat",
    "lon",
    "owner_name",
    "phone",
    "email",
    "contact_source",
    "notes",
]

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_row(csv_path: str, row: Dict, encoding: str):
    ensure_dir(csv_path)
    exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding=encoding) as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)