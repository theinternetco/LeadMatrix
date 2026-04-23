# ============================================================
# LeadMatrix - Auto-Update businesses.gmb_url in PostgreSQL
# FIXED: column name business_name (not businessname)
# Run: python update_gmb_urls_in_db.py
# ============================================================

import json
import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(BASE_DIR, "gmb_locations.json")

load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "dbname":   os.getenv("DB_NAME", "leadmatrix"),
    "user":     os.getenv("DB_USER", "leadmatrixuser"),
    "password": os.getenv("DB_PASSWORD", ""),
}

print("\n" + "="*60)
print("  LeadMatrix - Update GMB URLs in Database")
print("="*60)

print("\n[1/4] Loading gmb_locations.json...")
with open(JSON_FILE, "r", encoding="utf-8") as f:
    locations = json.load(f)
print(f"  Loaded {len(locations)} GMB locations")

print("\n[2/4] Connecting to PostgreSQL...")
conn   = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
print("  Connected OK")

print("\n[3/4] Fetching businesses from DB...")
cursor.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'businesses'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cursor.fetchall()]
print(f"  DB columns: {cols}")

name_col    = "business_name" if "business_name" in cols else "name"
phone_col   = "phone_number"  if "phone_number"  in cols else ("phone" if "phone" in cols else None)
website_col = "website"       if "website"        in cols else None
status_col  = "status"        if "status"         in cols else None

print(f"  Using: name={name_col} | phone={phone_col} | website={website_col}")

select_cols = f"id, name, {name_col}"
select_cols += f", {phone_col}" if phone_col else ", NULL"
select_cols += f", {website_col}" if website_col else ", NULL"

where = "WHERE status = 'active'" if status_col else ""
cursor.execute(f"SELECT {select_cols} FROM businesses {where}")
db_businesses = cursor.fetchall()
print(f"  Found {len(db_businesses)} active businesses")

print("\n[4/4] Matching & updating gmb_url...\n")

matched   = []
unmatched = []

def normalize(s):
    if not s: return ""
    s = s.lower().strip()
    for c in ["|", "-", ",", ".", "&", "(", ")", "/"]:
        s = s.replace(c, " ")
    return " ".join(s.split())

def phone_normalize(p):
    if not p: return ""
    return "".join(filter(str.isdigit, str(p)))[-10:]

def clean_url(u):
    return (u or "").lower().strip("/").replace("https://","").replace("http://","").replace("www.","")

for row in db_businesses:
    biz_id, biz_name, biz_bname, biz_phone, biz_website = row
    name_to_use = biz_bname or biz_name or ""
    norm_db     = normalize(name_to_use)
    norm_phone  = phone_normalize(biz_phone)
    best_match  = None
    best_score  = 0

    for loc in locations:
        norm_loc  = normalize(loc["business_name"])
        loc_phone = phone_normalize(loc.get("phone", ""))
        score     = 0

        db_words  = set(norm_db.split())
        loc_words = set(norm_loc.split())
        common    = db_words & loc_words
        if len(db_words) > 0:
            score += (len(common) / len(db_words)) * 60

        if norm_phone and loc_phone and norm_phone == loc_phone:
            score += 40

        biz_site = clean_url(biz_website)
        loc_site = clean_url(loc.get("website",""))
        if biz_site and loc_site and biz_site not in ("n/a","") and biz_site == loc_site:
            score += 30

        if score > best_score:
            best_score = score
            best_match = loc

    if best_match and best_score >= 40:
        gmb_url = best_match["gmb_url"]
        cursor.execute("UPDATE businesses SET gmb_url = %s WHERE id = %s", (gmb_url, biz_id))
        matched.append({"id": biz_id, "db_name": name_to_use, "gmb": best_match["business_name"], "url": gmb_url, "score": round(best_score, 1)})
        print(f"  [OK] #{biz_id:<3} Score:{round(best_score,1):<5}")
        print(f"       DB  : {name_to_use[:65]}")
        print(f"       GMB : {best_match['business_name'][:65]}")
        print(f"       URL : {gmb_url}\n")
    else:
        unmatched.append({"id": biz_id, "name": name_to_use, "score": round(best_score, 1)})

conn.commit()

print("="*60)
print(f"  MATCHED & Updated : {len(matched)}")
print(f"  NOT Matched       : {len(unmatched)}")
print("="*60)

if unmatched:
    print("\n  Businesses needing MANUAL mapping:")
    for b in unmatched:
        print(f"    ID {b['id']:>3} | Score {b['score']:>5} | {b['name'][:60]}")

print("\n  Verifying updated records...")
cursor.execute(f"""
    SELECT id, COALESCE({name_col}, name) as name, gmb_url
    FROM businesses
    WHERE gmb_url IS NOT NULL AND gmb_url LIKE 'accounts/%'
    ORDER BY id
""")
rows = cursor.fetchall()
print(f"\n  {len(rows)} businesses now have valid gmb_url:\n")
for row in rows:
    print(f"    #{row[0]:>3} | {str(row[1])[:45]:<45} | {row[2]}")

cursor.close()
conn.close()
print("\n  DONE! Run post_all_businesses.ps1 to post to all!")
print("="*60 + "\n")
