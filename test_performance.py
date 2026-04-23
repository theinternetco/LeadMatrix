import json
import csv
import calendar
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


creds = Credentials.from_authorized_user_file('token.json')
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    with open('token.json', 'w') as f:
        json.dump({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': list(creds.scopes)
        }, f, indent=2)


headers = {'Authorization': f'Bearer {creds.token}'}


def get_all_locations():
    locations = []
    url = "https://mybusinessbusinessinformation.googleapis.com/v1/accounts/114295392753759292048/locations"
    params = {'readMask': 'name,title', 'pageSize': 100}
    while True:
        r = requests.get(url, params=params, headers=headers)
        data = r.json()
        locations.extend(data.get('locations', []))
        next_token = data.get('nextPageToken')
        if not next_token:
            break
        params['pageToken'] = next_token
    return locations


MONTHS = [
    (2026, 2, 'FEB'),
    (2026, 3, 'MAR'),
]


# ✅ ADDED: BUSINESS_CONVERSATIONS and BUSINESS_BOOKINGS
metrics = [
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_DIRECTION_REQUESTS",
    "BUSINESS_CONVERSATIONS",   # ← Chat Clicks / Messages
    "BUSINESS_BOOKINGS",        # ← Bookings
]


def get_metric_monthly(location_name, metric, year, month):
    last_day = calendar.monthrange(year, month)[1]
    url = f"https://businessprofileperformance.googleapis.com/v1/{location_name}:getDailyMetricsTimeSeries"
    params = {
        'dailyMetric': metric,
        'dailyRange.startDate.year': year,
        'dailyRange.startDate.month': month,
        'dailyRange.startDate.day': 1,
        'dailyRange.endDate.year': year,
        'dailyRange.endDate.month': month,
        'dailyRange.endDate.day': last_day,
    }
    r = requests.get(url, params=params, headers=headers)
    data = r.json()
    if 'error' in data:
        return 0, data['error']['message']
    values = data.get('timeSeries', {}).get('datedValues', [])
    total = sum(int(v.get('value', 0)) for v in values if v.get('value'))

    # ✅ ADDED: Print raw daily values for conversations & bookings to debug
    if metric in ("BUSINESS_CONVERSATIONS", "BUSINESS_BOOKINGS"):
        raw_daily = {
            f"{v['date']['year']}-{str(v['date']['month']).zfill(2)}-{str(v['date']['day']).zfill(2)}": int(v.get('value', 0) or 0)
            for v in values if v.get('date')
        }
        non_zero = {k: val for k, val in raw_daily.items() if val > 0}
        if non_zero:
            print(f"      [DEBUG] {metric} non-zero days: {non_zero}")
        else:
            print(f"      [DEBUG] {metric}: all days returned 0 or empty — metric may not be enabled on GMB")

    return total, None


print("\n GMB INTERACTION TEST DATA (with Conversations + Bookings)")
print("=" * 70)


locations = get_all_locations()
print(f"Found {len(locations)} locations\n")


all_results = []


for loc in locations:
    location_name = loc['name']
    business_name = loc['title']

    print(f"  {business_name}")

    loc_result = {
        'business': business_name,
        'location': location_name,
    }

    for year, month, label in MONTHS:
        for metric in metrics:
            total, error = get_metric_monthly(location_name, metric, year, month)
            key = f'{metric}_{label}'
            if error:
                print(f"   ERROR {key}: {error}")
            else:
                print(f"   OK {key}: {total}")
            loc_result[key] = total

        loc_result[f'PHONE_CALLS_{label}']       = loc_result.get(f'CALL_CLICKS_{label}', 0)
        loc_result[f'DIRECTIONS_{label}']         = loc_result.get(f'BUSINESS_DIRECTION_REQUESTS_{label}', 0)
        loc_result[f'WEBSITE_CLICKS_{label}']     = loc_result.get(f'WEBSITE_CLICKS_{label}', 0)
        # ✅ ADDED: pull conversations and bookings per month
        loc_result[f'CONVERSATIONS_{label}']      = loc_result.get(f'BUSINESS_CONVERSATIONS_{label}', 0)
        loc_result[f'BOOKINGS_{label}']           = loc_result.get(f'BUSINESS_BOOKINGS_{label}', 0)
        loc_result[f'BUSINESS_PROFILE_INTERACTIONS_{label}'] = (
            loc_result[f'PHONE_CALLS_{label}'] +
            loc_result[f'DIRECTIONS_{label}'] +
            loc_result[f'WEBSITE_CLICKS_{label}'] +
            loc_result[f'CONVERSATIONS_{label}'] +
            loc_result[f'BOOKINGS_{label}']
        )

        print(f"   PHONE CALLS {label}:    {loc_result[f'PHONE_CALLS_{label}']}")
        print(f"   DIRECTIONS {label}:     {loc_result[f'DIRECTIONS_{label}']}")
        print(f"   WEBSITE CLICKS {label}: {loc_result[f'WEBSITE_CLICKS_{label}']}")
        print(f"   CONVERSATIONS {label}:  {loc_result[f'CONVERSATIONS_{label}']}")
        print(f"   BOOKINGS {label}:       {loc_result[f'BOOKINGS_{label}']}")
        print(f"   INTERACTIONS {label}:   {loc_result[f'BUSINESS_PROFILE_INTERACTIONS_{label}']}")

    # ✅ ADDED: overall totals include conversations + bookings
    loc_result['PHONE_CALLS_OVERALL']       = loc_result.get('PHONE_CALLS_FEB', 0)       + loc_result.get('PHONE_CALLS_MAR', 0)
    loc_result['DIRECTIONS_OVERALL']        = loc_result.get('DIRECTIONS_FEB', 0)        + loc_result.get('DIRECTIONS_MAR', 0)
    loc_result['WEBSITE_CLICKS_OVERALL']    = loc_result.get('WEBSITE_CLICKS_FEB', 0)    + loc_result.get('WEBSITE_CLICKS_MAR', 0)
    loc_result['CONVERSATIONS_OVERALL']     = loc_result.get('CONVERSATIONS_FEB', 0)     + loc_result.get('CONVERSATIONS_MAR', 0)
    loc_result['BOOKINGS_OVERALL']          = loc_result.get('BOOKINGS_FEB', 0)          + loc_result.get('BOOKINGS_MAR', 0)
    loc_result['BUSINESS_PROFILE_INTERACTIONS_OVERALL'] = (
        loc_result['PHONE_CALLS_OVERALL'] +
        loc_result['DIRECTIONS_OVERALL'] +
        loc_result['WEBSITE_CLICKS_OVERALL'] +
        loc_result['CONVERSATIONS_OVERALL'] +
        loc_result['BOOKINGS_OVERALL']
    )

    print(f"   TOTAL PHONE CALLS:    {loc_result['PHONE_CALLS_OVERALL']}")
    print(f"   TOTAL DIRECTIONS:     {loc_result['DIRECTIONS_OVERALL']}")
    print(f"   TOTAL WEBSITE CLICKS: {loc_result['WEBSITE_CLICKS_OVERALL']}")
    print(f"   TOTAL CONVERSATIONS:  {loc_result['CONVERSATIONS_OVERALL']}")
    print(f"   TOTAL BOOKINGS:       {loc_result['BOOKINGS_OVERALL']}")
    print(f"   TOTAL INTERACTIONS:   {loc_result['BUSINESS_PROFILE_INTERACTIONS_OVERALL']}")
    print()

    all_results.append(loc_result)


with open('gmb_interaction_test.json', 'w') as f:
    json.dump(all_results, f, indent=2)


# ✅ ADDED: conversations + bookings columns in CSV
fieldnames = [
    'business', 'location',
    'PHONE_CALLS_FEB', 'DIRECTIONS_FEB', 'WEBSITE_CLICKS_FEB', 'CONVERSATIONS_FEB', 'BOOKINGS_FEB', 'BUSINESS_PROFILE_INTERACTIONS_FEB',
    'PHONE_CALLS_MAR', 'DIRECTIONS_MAR', 'WEBSITE_CLICKS_MAR', 'CONVERSATIONS_MAR', 'BOOKINGS_MAR', 'BUSINESS_PROFILE_INTERACTIONS_MAR',
    'PHONE_CALLS_OVERALL', 'DIRECTIONS_OVERALL', 'WEBSITE_CLICKS_OVERALL', 'CONVERSATIONS_OVERALL', 'BOOKINGS_OVERALL', 'BUSINESS_PROFILE_INTERACTIONS_OVERALL',
]


with open('gmb_interaction_test.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(all_results)


print("=" * 70)
print(f"Done! {len(all_results)} businesses saved to:")
print("   gmb_interaction_test.json")
print("   gmb_interaction_test.csv")
print()
print("KEY — Check the [DEBUG] lines above for each business:")
print("   Non-zero days shown  = Google HAS data, run push_to_db.py to sync")
print("   'all days returned 0' = Messaging/Bookings not enabled on that GMB profile")
