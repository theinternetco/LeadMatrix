# E:\LEADMATRIX-API\app\scraper\fetch_metrics.py

"""
Fetch GMB Performance Metrics for all locations
Gets: Full location details with correct field names
"""

import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import logging
import json
import csv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/business.manage']

class GMBMetricsFetcher:
    """
    Fetch performance metrics for GMB locations
    """
    
    def __init__(self, token_path: str = 'token.pickle'):
        self.token_path = token_path
        self.service = None
        
    def authenticate(self):
        """Load existing token and build service"""
        if not os.path.exists(self.token_path):
            logger.error("❌ Token not found. Run gmb_performance.py first!")
            return False
        
        with open(self.token_path, 'rb') as token:
            creds = pickle.load(token)
        
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        
        try:
            self.service = build('mybusinessbusinessinformation', 'v1', credentials=creds)
            logger.info("✅ API service initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed: {e}")
            return False
    
    def get_location_details(self, location_id: str):
        """
        Get detailed information for a location
        
        Args:
            location_id: Format 'locations/xxxxx'
            
        Returns:
            dict: Location details
        """
        try:
            # Correct field mask for API v1
            location = self.service.locations().get(
                name=location_id,
                readMask="name,title,storefrontAddress,phoneNumbers,websiteUri,categories,profile"
            ).execute()
            
            # Extract phone number safely
            phone_numbers = location.get('phoneNumbers', {})
            primary_phone = phone_numbers.get('primaryPhone', 'N/A')
            
            # Extract address
            address = location.get('storefrontAddress', {})
            address_lines = address.get('addressLines', [])
            full_address = ', '.join(address_lines) if address_lines else 'N/A'
            
            # Extract categories
            categories = location.get('categories', {})
            primary_category = categories.get('primaryCategory', {}).get('displayName', 'N/A')
            
            return {
                'location_id': location.get('name', 'N/A'),
                'business_name': location.get('title', 'N/A'),
                'address': full_address,
                'city': address.get('locality', 'N/A'),
                'state': address.get('administrativeArea', 'N/A'),
                'postal_code': address.get('postalCode', 'N/A'),
                'country': address.get('regionCode', 'N/A'),
                'phone': primary_phone,
                'website': location.get('websiteUri', 'N/A'),
                'category': primary_category,
                'description': location.get('profile', {}).get('description', 'N/A')
            }
        except Exception as e:
            logger.error(f"❌ Error fetching location {location_id}: {e}")
            return None


# Main execution
if __name__ == "__main__":
    print("\n" + "="*70)
    print("📊 GMB PERFORMANCE METRICS FETCHER")
    print("="*70 + "\n")
    
    fetcher = GMBMetricsFetcher()
    
    if fetcher.authenticate():
        # Your 10 location IDs from the test
        location_ids = [
            "locations/6579386014873909971",  # Dr Zahir Abbas
            "locations/13380490170307176042",  # Dr Ankit Biyani
            "locations/13670040869331009286",  # Fertility Square
            "locations/12699816568782190708",  # Dr. Garima
            "locations/6399916511842467310",   # Digiscrub
            "locations/18010961921854578173",  # Essas Club
            "locations/12588517315963465656",  # AUM ENT Clinic
            "locations/15448129543872560319",  # Deevine Eye Care
            "locations/3336330716982602533",   # The Internet Co
            "locations/6825341591892205881",   # Dr. Prashansa
        ]
        
        print("🔍 Fetching detailed information for all 10 locations...\n")
        print("-" * 70)
        
        all_locations = []
        
        for idx, loc_id in enumerate(location_ids, 1):
            details = fetcher.get_location_details(loc_id)
            
            if details:
                all_locations.append(details)
                
                print(f"\n✅ {idx}. {details['business_name']}")
                print(f"   📍 Address: {details['address']}")
                print(f"   🏙️  City: {details['city']}, {details['state']} - {details['postal_code']}")
                print(f"   📞 Phone: {details['phone']}")
                print(f"   🌐 Website: {details['website']}")
                print(f"   🏷️  Category: {details['category']}")
        
        print("\n" + "="*70)
        
        if all_locations:
            # Save to JSON
            output_file = 'gmb_locations.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_locations, f, indent=2, ensure_ascii=False)
            
            print(f"✅ SUCCESS! Saved {len(all_locations)} locations to {output_file}")
            
            # Save to CSV
            csv_file = 'gmb_locations.csv'
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_locations[0].keys())
                writer.writeheader()
                writer.writerows(all_locations)
            
            print(f"✅ Also saved to {csv_file}")
            
            print("\n📊 SUMMARY:")
            print(f"   Total Locations: {len(all_locations)}")
            print(f"   Healthcare Businesses: {sum(1 for loc in all_locations if 'dr' in loc['business_name'].lower() or 'clinic' in loc['business_name'].lower())}")
            print(f"   With Websites: {sum(1 for loc in all_locations if loc['website'] != 'N/A')}")
            print(f"   With Phones: {sum(1 for loc in all_locations if loc['phone'] != 'N/A')}")
        else:
            print("❌ No locations fetched. Check API permissions.")
        
        print("="*70 + "\n")
    else:
        print("❌ Authentication failed. Run gmb_performance.py first!")
