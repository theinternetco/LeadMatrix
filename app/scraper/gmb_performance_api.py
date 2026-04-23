# E:\LEADMATRIX-API\app\scraper\gmb_performance_api.py

"""
GMB Performance Fetcher with Date Range Support
Fetches business data and attempts to get performance metrics
"""

import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

print("\n" + "="*70)
print("📊 GMB PERFORMANCE FETCHER WITH METRICS")
print("="*70 + "\n")

# Authentication
SCOPES = ['https://www.googleapis.com/auth/business.manage']

def authenticate():
    """Authenticate with Google"""
    creds = None
    
    if os.path.exists('token.pickle'):
        print("🔐 Loading existing credentials...")
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("✅ Authentication successful!\n")
    return creds

def get_performance_metrics(creds, account_id, location_id, start_date, end_date):
    """
    Try to fetch performance metrics using MY Business API v4
    
    Args:
        creds: Google credentials
        account_id: Account ID (e.g., "accounts/xxx")
        location_id: Location ID
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        dict: Performance metrics or None
    """
    try:
        print("📊 Attempting to fetch performance metrics...")
        
        # Build v4 service for insights
        service_v4 = build('mybusiness', 'v4', credentials=creds)
        
        # Format dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        full_location_id = f"{account_id}/locations/{location_id}"
        
        # Request body
        request_body = {
            "locationNames": [full_location_id],
            "basicRequest": {
                "metricRequests": [
                    {"metric": "QUERIES_DIRECT"},
                    {"metric": "QUERIES_INDIRECT"},
                    {"metric": "VIEWS_MAPS"},
                    {"metric": "VIEWS_SEARCH"},
                    {"metric": "ACTIONS_WEBSITE"},
                    {"metric": "ACTIONS_PHONE"},
                    {"metric": "ACTIONS_DRIVING_DIRECTIONS"},
                ],
                "timeRange": {
                    "startTime": start.strftime('%Y-%m-%dT00:00:00Z'),
                    "endTime": end.strftime('%Y-%m-%dT23:59:59Z')
                }
            }
        }
        
        # Fetch insights
        response = service_v4.accounts().locations().reportInsights(
            name=account_id,
            body=request_body
        ).execute()
        
        print("✅ Performance metrics fetched!\n")
        
        # Parse metrics
        metrics = {}
        if 'locationMetrics' in response:
            for location_data in response['locationMetrics']:
                for metric_value in location_data.get('metricValues', []):
                    metric_name = metric_value.get('metric')
                    total_value = metric_value.get('totalValue', {}).get('value', 0)
                    metrics[metric_name] = total_value
        
        return metrics
        
    except Exception as e:
        print(f"⚠️  Performance metrics unavailable: {str(e)[:100]}")
        print("   (Google has restricted this API for most accounts)\n")
        return None

# Main execution
try:
    # Authenticate
    creds = authenticate()
    
    # Build service
    print("🔨 Building API service...")
    service = build('mybusinessbusinessinformation', 'v1', credentials=creds)
    print("✅ Service ready!\n")
    
    # ===== CONFIGURE YOUR BUSINESS =====
    ACCOUNT_ID = "accounts/114295392753759292048"
    LOCATION_ID = "6825341591892205881"  # Dr. Prashansa
    
    # ===== CONFIGURE DATE RANGE =====
    END_DATE = datetime.now().strftime('%Y-%m-%d')
    START_DATE = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    print(f"📍 Fetching data for: locations/{LOCATION_ID}")
    print(f"📅 Date Range: {START_DATE} to {END_DATE}\n")
    
    # Fetch basic location data - FIXED: Use correct format
    print("📥 Fetching business profile data...")
    location = service.locations().get(
        name=f"locations/{LOCATION_ID}",  # ← FIXED: Correct format for v1 API
        readMask="name,title,storefrontAddress,phoneNumbers,websiteUri,categories,metadata,regularHours"
    ).execute()
    
    print("✅ Profile data fetched successfully!\n")
    
    # Try to fetch performance metrics
    performance_metrics = get_performance_metrics(
        creds, ACCOUNT_ID, LOCATION_ID, START_DATE, END_DATE
    )
    
    # Display results
    print("="*70)
    print("📊 BUSINESS PROFILE & PERFORMANCE REPORT")
    print("="*70 + "\n")
    
    print(f"Business Name:  {location.get('title', 'N/A')}")
    print(f"Location ID:    {location.get('name', 'N/A')}")
    
    # Address
    address = location.get('storefrontAddress', {})
    if address:
        addr_lines = ', '.join(address.get('addressLines', []))
        city = address.get('locality', '')
        state = address.get('administrativeArea', '')
        postal = address.get('postalCode', '')
        print(f"\nAddress:        {addr_lines}")
        print(f"City:           {city}, {state} - {postal}")
    
    # Contact
    phones = location.get('phoneNumbers', {})
    if phones:
        print(f"\nPhone:          {phones.get('primaryPhone', 'N/A')}")
    
    website = location.get('websiteUri', 'N/A')
    print(f"Website:        {website}")
    
    # Category
    categories = location.get('categories', {})
    primary = categories.get('primaryCategory', {}).get('displayName', 'N/A')
    print(f"\nCategory:       {primary}")
    
    # Business Hours
    hours = location.get('regularHours', {})
    if hours and 'periods' in hours:
        print(f"\n🕒 BUSINESS HOURS:")
        day_map = {'MONDAY': 'Mon', 'TUESDAY': 'Tue', 'WEDNESDAY': 'Wed', 
                   'THURSDAY': 'Thu', 'FRIDAY': 'Fri', 'SATURDAY': 'Sat', 'SUNDAY': 'Sun'}
        for period in hours['periods'][:3]:  # Show first 3 days
            day = day_map.get(period.get('openDay', ''), period.get('openDay', ''))
            open_time = period.get('openTime', 'N/A')
            close_time = period.get('closeTime', 'N/A')
            print(f"   {day}: {open_time} - {close_time}")
    
    # Metadata
    meta = location.get('metadata', {})
    if meta:
        print(f"\n📱 PROFILE STATUS:")
        print(f"   Can Receive Calls:  {meta.get('canHaveBusinessCalls', False)}")
        print(f"   Google Updated:     {meta.get('hasGoogleUpdated', False)}")
        maps_url = meta.get('mapsUri', 'N/A')
        if maps_url != 'N/A':
            print(f"   Maps URL:           {maps_url[:50]}...")
    
    # Performance Metrics
    if performance_metrics:
        print(f"\n📊 PERFORMANCE METRICS ({START_DATE} to {END_DATE}):")
        print(f"   Direct Searches:    {performance_metrics.get('QUERIES_DIRECT', 0)}")
        print(f"   Discovery Searches: {performance_metrics.get('QUERIES_INDIRECT', 0)}")
        print(f"   Maps Views:         {performance_metrics.get('VIEWS_MAPS', 0)}")
        print(f"   Search Views:       {performance_metrics.get('VIEWS_SEARCH', 0)}")
        print(f"   Website Clicks:     {performance_metrics.get('ACTIONS_WEBSITE', 0)}")
        print(f"   Phone Calls:        {performance_metrics.get('ACTIONS_PHONE', 0)}")
        print(f"   Directions:         {performance_metrics.get('ACTIONS_DRIVING_DIRECTIONS', 0)}")
        
        # Calculate totals
        total_views = performance_metrics.get('VIEWS_MAPS', 0) + performance_metrics.get('VIEWS_SEARCH', 0)
        total_actions = (performance_metrics.get('ACTIONS_WEBSITE', 0) + 
                        performance_metrics.get('ACTIONS_PHONE', 0) + 
                        performance_metrics.get('ACTIONS_DRIVING_DIRECTIONS', 0))
        
        print(f"\n   📈 Total Views:     {total_views}")
        print(f"   ⚡ Total Actions:   {total_actions}")
    else:
        print(f"\n⚠️  PERFORMANCE METRICS: Not Available")
        print(f"   Date Range: {START_DATE} to {END_DATE}")
        print(f"   Reason: API access restricted by Google")
    
    print("\n" + "="*70)
    
    # Save to file
    output = {
        'business_name': location.get('title'),
        'location_id': location.get('name'),
        'date_range': {
            'start': START_DATE,
            'end': END_DATE
        },
        'profile_data': {
            'address': address,
            'phone': phones.get('primaryPhone') if phones else None,
            'website': website,
            'category': primary,
            'metadata': meta
        },
        'performance_metrics': performance_metrics,
        'fetched_at': datetime.now().isoformat()
    }
    
    filename = f"gmb_complete_{LOCATION_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Saved to: {filename}")
    print("="*70 + "\n")
    
    if performance_metrics:
        print("✅ SUCCESS! Business profile & performance metrics fetched.")
    else:
        print("✅ SUCCESS! Business profile fetched.")
        print("\n💡 NOTE: To get performance metrics, you need:")
        print("   1. Google Partner API access (restricted)")
        print("   2. OR use Selenium to scrape GMB dashboard")
        print("   3. OR manually export from business.google.com")
    
    print("\n")

except FileNotFoundError:
    print("\n❌ ERROR: credentials.json not found!")
    print("   Make sure credentials.json is in the current directory")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n💡 TIP: Make sure you have:")
    print("   1. credentials.json in the current directory")
    print("   2. Internet connection")
    print("   3. pip install google-auth-oauthlib google-api-python-client")

print("\n")
