import requests

API_BASE = "http://localhost:8000"
DAYS = 30

# Step 1: fetch all businesses
businesses = requests.get(f"{API_BASE}/api/businesses", timeout=10).json()
print(f"Found {len(businesses)} businesses\n")

# Step 2: check analytics for each
for biz in businesses:
    bid = biz["id"]
    name = biz.get("name", "Unknown")
    try:
        r = requests.get(f"{API_BASE}/api/analytics/{bid}", params={"days": DAYS}, timeout=10).json()
        m = r.get("metrics", {})
        trends = r.get("daily_trends", [])
        days_with_data = sum(1 for d in trends if any([d.get("phone_calls"), d.get("directions"), d.get("website_clicks")]))

        print(f"[{bid}] {name}")
        print(f"  ✅ success={r.get('success')}  days_with_data={days_with_data}/{DAYS}")
        print(f"  📞 Calls={m.get('total_phone_calls',0)}  📍 Directions={m.get('total_directions',0)}  🌐 Clicks={m.get('total_website_clicks',0)}")
        print(f"  🔁 Profile Interactions={m.get('total_profile_interactions',0)}")

        if days_with_data == 0:
            print(f"  ⚠️  NO DATA — business has 0 days with any activity")
        if not r.get("success"):
            print(f"  ❌ success=False — check your DB query for this ID")
    except Exception as e:
        print(f"  ❌ ERROR for business {bid}: {e}")
    print()