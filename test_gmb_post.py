import json
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

creds = Credentials.from_authorized_user_file('token.json')
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

headers = {
    "Authorization": f"Bearer {creds.token}",
    "Content-Type": "application/json"
}

# ✅ FIXED — must include full path: accounts/ACCOUNT_ID/locations/LOCATION_ID
ACCOUNT_ID  = "114295392753759292048"
LOCATION_ID = "6579386014873909971"   # Dr Zahir Abbas — from your DB

url = f"https://mybusiness.googleapis.com/v4/accounts/{ACCOUNT_ID}/locations/{LOCATION_ID}/localPosts"

payload = {
    "languageCode": "en",
    "summary": "This is a TEST post from LeadMatrix API. Please ignore. Will be deleted.",
    "topicType": "STANDARD",
    "callToAction": {
        "actionType": "LEARN_MORE",
        "url": "https://google.com"
    }
}

r = requests.post(url, json=payload, headers=headers)

print(f"Status Code : {r.status_code}")
print(f"Raw Body    : {r.text[:800]}")

if r.status_code == 200:
    data = r.json()
    print(f"\n✅ SUCCESS! Post created: {data.get('name')}")
else:
    print(f"\n❌ FAILED — Status {r.status_code}")