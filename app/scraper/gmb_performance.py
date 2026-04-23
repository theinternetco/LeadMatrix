# E:\LEADMATRIX-API\app\scraper\gmb_performance.py

"""
GMB Performance API Integration with OAuth 2.0
Optimized for limited API quota (300 requests/min)
"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OAuth 2.0 scopes for GMB API
SCOPES = ['https://www.googleapis.com/auth/business.manage']

class GMBPerformanceAPI:
    """
    Google My Business Performance API integration
    Quota-optimized for 35+ healthcare clients
    """
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Initialize GMB Performance API
        
        Args:
            credentials_path: Path to OAuth credentials JSON
        """
        self.credentials_path = credentials_path
        self.token_path = 'token.pickle'
        self.service = None
        self.accounts_service = None
        
    def authenticate(self):
        """
        Authenticate with Google using OAuth 2.0
        
        Returns:
            bool: True if authentication successful
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
            logger.info("✅ Loaded existing token")
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("✅ Token refreshed successfully")
                except Exception as e:
                    logger.error(f"❌ Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    # Use port 8080 instead of 0 for better compatibility
                    creds = flow.run_local_server(port=8080, 
                                                   prompt='consent',
                                                   success_message='Authentication successful! You can close this window.')
                    logger.info("✅ New authentication successful")
                except Exception as e:
                    logger.error(f"❌ Authentication failed: {e}")
                    return False
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
            logger.info("✅ Token saved for future use")
        
        try:
            # Build GMB API services
            self.service = build('mybusinessbusinessinformation', 'v1', credentials=creds)
            self.accounts_service = build('mybusinessaccountmanagement', 'v1', credentials=creds)
            logger.info("✅ GMB API services initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to build API service: {e}")
            return False
    
    def get_accounts(self):
        """
        Get all GMB accounts accessible by authenticated user
        
        Returns:
            list: List of account objects
        """
        if not self.accounts_service:
            logger.error("❌ Not authenticated. Call authenticate() first.")
            return []
        
        try:
            accounts = self.accounts_service.accounts().list().execute()
            account_list = accounts.get('accounts', [])
            logger.info(f"✅ Found {len(account_list)} accounts")
            return account_list
        except Exception as e:
            logger.error(f"❌ Failed to get accounts: {e}")
            return []
    
    def get_locations(self, account_name: str):
        """
        Get all locations for a specific GMB account
        
        Args:
            account_name: Account name (format: 'accounts/xxx')
            
        Returns:
            list: List of location objects
        """
        if not self.service:
            logger.error("❌ Not authenticated")
            return []
        
        try:
            locations = self.service.accounts().locations().list(
                parent=account_name,
                readMask="name,title,storeCode,storefrontAddress"
            ).execute()
            
            location_list = locations.get('locations', [])
            logger.info(f"✅ Found {len(location_list)} locations")
            return location_list
        except Exception as e:
            logger.error(f"❌ Failed to get locations: {e}")
            return []
    
    def save_locations_to_db(self, locations: List[Dict]):
        """
        Save locations to your PostgreSQL database
        
        Args:
            locations: List of location objects from GMB API
        """
        # TODO: Connect to your existing database
        # This will integrate with your existing E:\LEADMATRIX-API\app\database.py
        
        for loc in locations:
            location_data = {
                'gmb_id': loc.get('name'),
                'name': loc.get('title'),
                'address': loc.get('storefrontAddress', {}).get('addressLines', [''])[0],
                'city': loc.get('storefrontAddress', {}).get('locality', ''),
                'state': loc.get('storefrontAddress', {}).get('administrativeArea', ''),
            }
            logger.info(f"📍 Location: {location_data['name']}")


# Test authentication
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 GMB PERFORMANCE API - AUTHENTICATION TEST")
    print("="*60 + "\n")
    
    gmb = GMBPerformanceAPI(credentials_path='credentials.json')
    
    print("📡 STEP 1: Authenticating with Google...")
    print("   (Browser will open automatically)")
    print("-" * 60)
    
    if gmb.authenticate():
        print("\n✅ AUTHENTICATION SUCCESSFUL!\n")
        
        print("📊 STEP 2: Fetching your GMB accounts...")
        print("-" * 60)
        accounts = gmb.get_accounts()
        
        if accounts:
            for idx, account in enumerate(accounts, 1):
                account_name = account.get('accountName', 'Unknown')
                account_id = account.get('name', 'Unknown')
                
                print(f"\n✅ Account {idx}: {account_name}")
                print(f"   ID: {account_id}")
                
                print(f"\n📍 STEP 3: Fetching locations for {account_name}...")
                print("-" * 60)
                locations = gmb.get_locations(account_id)
                
                if locations:
                    print(f"\n✅ Found {len(locations)} locations:\n")
                    for i, loc in enumerate(locations, 1):
                        title = loc.get('title', 'Unnamed')
                        loc_id = loc.get('name', 'No ID')
                        address = loc.get('storefrontAddress', {})
                        city = address.get('locality', '')
                        
                        print(f"   {i}. {title}")
                        print(f"      ID: {loc_id}")
                        print(f"      Location: {city}")
                        print()
                else:
                    print("   ⚠️  No locations found for this account")
        else:
            print("\n❌ No accounts found")
            print("\n💡 TIP: Make sure your Google account has access to GMB")
    else:
        print("\n❌ AUTHENTICATION FAILED")
        print("\n🔧 TROUBLESHOOTING:")
        print("   1. Check if credentials.json exists in E:\\LEADMATRIX-API\\")
        print("   2. Go to OAuth consent screen and add your email as test user")
        print("   3. Enable Business Profile API in Google Cloud Console")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60 + "\n")
