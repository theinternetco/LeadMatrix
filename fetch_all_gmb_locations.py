# ============================================================
# LeadMatrix - Fetch ALL 44 GMB Locations from Google API
# Saves to gmb_locations.json + gmb_locations.csv
# Run: python fetch_all_gmb_locations.py
# ============================================================

import json
import csv
import os
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE  = os.path.join(BASE_DIR, "token.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "gmb_locations.json")
OUTPUT_CSV  = os.path.join(BASE_DIR, "gmb_locations.csv")

print("\n" + "="*60)
print("  LeadMatrix - Fetch ALL GMB Locations")
print("="*60)

# ── Load & Refresh Token ─────────────────────────────────────
print("\n[1/4] Loading token...")
gmb_token_json = os.getenv("GMB_TOKEN_JSON")
if gmb_token_json:
    token_data = json.loads(gmb_token_json)
elif os.path.exists(TOKEN_FILE):
    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)
else:
    raise FileNotFoundError("No token found. Set GMB_TOKEN_JSON env var or provide token.json.")

creds = Credentials(
    token         = token_data.get("token"),
    refresh_token = token_data.get("refresh_token"),
    token_uri     = token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
    client_id     = token_data.get("client_id"),
    client_secret = token_data.get("client_secret"),
    scopes        = token_data.get("scopes", ["https://www.googleapis.com/auth/business.manage"])
)

if creds.expired and creds.refresh_token:
    print("  Token expired — refreshing...")
    creds.refresh(Request())
    token_data["token"] = creds.token
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    print("  Token refreshed & saved OK")
else:
    print("  Token valid OK")

headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json"
}

# ── Step 2: Get All Accounts ─────────────────────────────────
print("\n[2/4] Fetching GMB accounts...")
accounts_url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
resp = requests.get(accounts_url, headers=headers)
resp.raise_for_status()
accounts = resp.json().get("accounts", [])
print(f"  Found {len(accounts)} account(s)")
for acc in accounts:
    print(f"  → {acc.get('name')} | {acc.get('accountName')} | Type: {acc.get('type')}")

# ── Step 3: Fetch ALL Locations ──────────────────────────────
print("\n[3/4] Fetching all locations...")
all_locations = []

for account in accounts:
    account_name = account.get("name")
    print(f"\n  Account: {account_name}")
    page_token = None
    page = 1

    while True:
        loc_url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/"
            f"{account_name}/locations"
            f"?readMask=name,title,phoneNumbers,websiteUri,categories,"
            f"storefrontAddress,regularHours,profile,metadata"
            f"&pageSize=100"
        )
        if page_token:
            loc_url += f"&pageToken={page_token}"

        resp = requests.get(loc_url, headers=headers)
        if resp.status_code != 200:
            print(f"  ERROR {resp.status_code}: {resp.text[:200]}")
            break

        data       = resp.json()
        locations  = data.get("locations", [])
        page_token = data.get("nextPageToken")
        print(f"  Page {page}: {len(locations)} locations")

        for loc in locations:
            loc_name    = loc.get("name", "")
            location_id = loc_name.replace(f"{account_name}/", "") if account_name in loc_name else loc_name

            addr     = loc.get("storefrontAddress", {})
            lines    = addr.get("addressLines", [])
            address  = ", ".join(lines) if lines else "N/A"
            city     = addr.get("locality", "N/A")
            state    = addr.get("administrativeArea", "N/A")
            postal   = addr.get("postalCode", "N/A")
            country  = addr.get("regionCode", "IN")

            phones   = loc.get("phoneNumbers", {})
            phone    = phones.get("primaryPhone", "N/A")
            website  = loc.get("websiteUri", "N/A")

            cats     = loc.get("categories", {})
            primary  = cats.get("primaryCategory", {})
            category = primary.get("displayName", "N/A")

            profile  = loc.get("profile", {})
            desc     = profile.get("description", "N/A")

            clean_loc_id = location_id.split("/")[-1] if "/" in location_id else location_id
            gmb_url      = f"{account_name}/locations/{clean_loc_id}"

            all_locations.append({
                "location_id":   f"locations/{clean_loc_id}",
                "gmb_url":       gmb_url,
                "account_name":  account_name,
                "business_name": loc.get("title", "N/A"),
                "address":       address,
                "city":          city,
                "state":         state,
                "postal_code":   postal,
                "country":       country,
                "phone":         phone,
                "website":       website,
                "category":      category,
                "description":   desc,
            })

        page += 1
        if not page_token:
            break

print(f"\n  Total locations fetched: {len(all_locations)}")

# ── Step 4: Save JSON + CSV ──────────────────────────────────
print("\n[4/4] Saving results...")
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(all_locations, f, indent=2, ensure_ascii=False)
print(f"  Saved JSON → {OUTPUT_JSON}")

if all_locations:
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_locations[0].keys())
        writer.writeheader()
        writer.writerows(all_locations)
    print(f"  Saved CSV  → {OUTPUT_CSV}")

print("\n" + "="*60)
print(f"  DONE! {len(all_locations)} locations saved")
print("="*60)
print(f"\n{'#':<4} {'Business Name':<50} {'City':<15} {'Location ID'}")
print("-"*100)
for i, loc in enumerate(all_locations, 1):
    name  = loc["business_name"][:48] + ".." if len(loc["business_name"]) > 48 else loc["business_name"]
    city  = loc["city"][:13]
    print(f"{i:<4} {name:<50} {city:<15} {loc['location_id']}")

print("\n  Next: Run  python update_gmb_urls_in_db.py")
print("="*60 + "\n")