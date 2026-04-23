# app/services/gmb_ranking_tracker.py
"""
✅ ULTIMATE INTERACTIVE GMB RANKING TRACKER v2.0
🎯 With Menu System + Multi-Location + Pagination Support
Integrated with FastAPI Backend
"""

# ============================================
# FALLBACK DUMMY CLASSES (IMPORT ERROR FIX)
# ============================================

class RankingTrackerService:
    """Fallback dummy class for RankingTrackerService"""
    def __init__(self, headless=False, use_google_search=False):
        self.headless = headless
        self.use_google_search = use_google_search
    
    def check_gmb_ranking(self, **kwargs):
        return {
            "found": False,
            "position": 0,
            "error": "RankingTrackerService not available"
        }
    
    def close(self):
        pass


# ============================================
# ACTUAL IMPLEMENTATION BELOW
# ============================================

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import pandas as pd
from datetime import datetime
import json
import os
from fake_useragent import UserAgent
import warnings
import logging
import atexit
import gc


warnings.filterwarnings("ignore")
logging.getLogger("undetected_chromedriver").setLevel(logging.CRITICAL)



def cleanup_on_exit():
    gc.collect()



atexit.register(cleanup_on_exit)



class AdvancedGMBRankingTracker:
    """🔥 ULTIMATE GMB Ranking Tracker with MULTI-PAGE PAGINATION SUPPORT"""
    
    def __init__(self, headless=False, use_google_search=True):
        self.headless = headless
        self.use_google_search = use_google_search
        self.ua = UserAgent()
        self.driver = None
        self.all_businesses = []
    
    def get_random_user_agent(self):
        return self.ua.random
    
    def setup_driver(self):
        """Advanced Driver Configuration with Anti-Detection"""
        options = uc.ChromeOptions()
        
        if self.headless:
            options.add_argument('--headless=new')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-extensions')
        options.add_argument('--profile-directory=Default')
        options.add_argument('--disable-gpu')
        
        screen_resolutions = [
            '--window-size=1920,1080',
            '--window-size=1366,768',
            '--window-size=1536,864',
        ]
        options.add_argument(random.choice(screen_resolutions))
        options.add_argument(f'user-agent={self.get_random_user_agent()}')
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "webrtc.ip_handling_policy": "disable_non_proxied_udp"
        }
        options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = uc.Chrome(options=options, version_main=None)
        except Exception as e:
            print(f"⚠️ Driver setup retry: {e}")
            time.sleep(2)
            self.driver = uc.Chrome(options=options, version_main=None)
        
        try:
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        except:
            pass
        
        return self.driver
    
    def human_like_delay(self, min_delay=2, max_delay=5):
        """Random human-like delays"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def move_mouse_randomly(self):
        """Random mouse movements"""
        try:
            actions = ActionChains(self.driver)
            for _ in range(random.randint(2, 5)):
                x_offset = random.randint(-100, 100)
                y_offset = random.randint(-100, 100)
                actions.move_by_offset(x_offset, y_offset).perform()
                time.sleep(random.uniform(0.1, 0.3))
        except:
            pass
    
    def scroll_smoothly(self, scrolls=5):
        """Smooth scrolling simulation"""
        for i in range(scrolls):
            scroll_amount = random.randint(300, 500)
            try:
                self.driver.execute_script(f'window.scrollBy(0, {scroll_amount})')
            except:
                pass
            time.sleep(random.uniform(0.3, 0.8))
    
    def check_gmb_ranking(self, keyword, location, business_name, business_names, max_results=100):
        """Main ranking check function"""
        self.all_businesses = []
        
        print(f"\n{'='*80}")
        print(f"🎯 TRACKING: {keyword}")
        print(f"   📍 Location: {location}")
        print(f"   🏢 Business: {business_name}")
        print(f"{'='*80}")
        
        try:
            if not self.driver:
                self.setup_driver()
            
            search_query = f"{keyword} in {location}"
            url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}&tbm=lcl"
            
            print(f"🌐 URL: {url}")
            
            self.driver.get(url)
            self.human_like_delay(5, 8)
            self.move_mouse_randomly()
            
            return self._track_multi_page_google_search(keyword, location, business_name, business_names, max_results)
        
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            return self._create_error_result(keyword, location, business_name, str(e))
    
    def _track_multi_page_google_search(self, keyword, location, business_name, business_names, max_results):
        """🔥 MULTI-PAGE TRACKING for Google Search"""
        position = 0
        checked_names = set()
        page_number = 1
        max_pages = 10
        
        while page_number <= max_pages and position < max_results:
            print(f"\n📄 === PAGE {page_number} ===")
            
            time.sleep(3)
            self.scroll_smoothly(3)
            time.sleep(2)
            
            business_selectors = [
                'div.VkpGBb',
                'div[jscontroller][data-hveid]',
                'div.rllt__details',
                'div[data-cid]',
            ]
            
            businesses = []
            for selector in business_selectors:
                try:
                    businesses = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if businesses:
                        print(f"   ✅ Found {len(businesses)} results on page {page_number}")
                        break
                except:
                    continue
            
            if not businesses:
                print(f"   ⚠️ No businesses found on page {page_number}")
                break
            
            new_results_found = False
            for business in businesses:
                try:
                    name = self._extract_business_name_search(business)
                    
                    if not name or name in checked_names:
                        continue
                    
                    checked_names.add(name)
                    position += 1
                    new_results_found = True
                    
                    self.all_businesses.append({
                        'position': position,
                        'name': name,
                        'page': page_number
                    })
                    
                    print(f"  #{position}: {name}")
                    
                    for business_name_check in business_names:
                        if self._is_business_match(business_name_check, name):
                            print(f"\n🎉 ✅ FOUND at Position #{position} (Page {page_number})")
                            print(f"   📍 Matched Name: {name}")
                            
                            return {
                                'keyword': keyword,
                                'location': location,
                                'searched_business': business_name,
                                'found_business_name': name,
                                'position': position,
                                'page': page_number,
                                'found': True,
                                'total_checked': position,
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                    
                    if position >= max_results:
                        break
                
                except:
                    continue
            
            if not new_results_found:
                print(f"   ⚠️ No new unique results on page {page_number}")
                break
            
            if position >= max_results:
                break
            
            next_button_found = self._click_next_page()
            
            if not next_button_found:
                print(f"\n   ⚠️ No 'Next' button found. Reached last page.")
                break
            
            page_number += 1
            self.human_like_delay(3, 5)
        
        print(f"\n❌ NOT FOUND in {position} results across {page_number} pages")
        return self._create_not_found_result(keyword, location, business_name, position)
    
    def _click_next_page(self):
        """Click the 'Next' button to navigate to next page"""
        next_button_selectors = [
            'a#pnnext',
            'a[aria-label="Next page"]',
            'a[aria-label="Next"]',
        ]
        
        for selector in next_button_selectors:
            try:
                next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                if next_button and next_button.is_displayed():
                    print(f"   🔄 Clicking 'Next' button...")
                    
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(1)
                    
                    try:
                        next_button.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", next_button)
                    
                    return True
            except:
                continue
        
        return False
    
    def _extract_business_name_search(self, business_element):
        """Extract business name from Google Search"""
        name_selectors = [
            'div[role="heading"]',
            'span.OSrXXb',
            'div.dbg0pd',
            'a span',
        ]
        
        for selector in name_selectors:
            try:
                element = business_element.find_element(By.CSS_SELECTOR, selector)
                name = element.text.strip() or element.get_attribute('aria-label')
                if name and len(name) > 3:
                    return name
            except:
                continue
        
        try:
            text = business_element.text.strip()
            if text:
                lines = text.split('\n')
                for line in lines[:3]:
                    if len(line) > 3 and len(line) < 100:
                        return line
        except:
            pass
        
        return None
    
    def _is_business_match(self, target_name, found_name):
        """Fuzzy matching with multiple strategies"""
        target_lower = target_name.lower()
        found_lower = found_name.lower()
        
        if target_lower == found_lower:
            return True
        
        if target_lower in found_lower or found_lower in target_lower:
            return True
        
        target_clean = self._clean_business_name(target_name)
        found_clean = self._clean_business_name(found_name)
        
        if target_clean in found_clean or found_clean in target_clean:
            return True
        
        target_terms = set(target_clean.split())
        found_terms = set(found_clean.split())
        common_terms = target_terms & found_terms
        
        if len(target_terms) > 0 and len(common_terms) / len(target_terms) >= 0.7:
            return True
        
        return False
    
    def _clean_business_name(self, name):
        """Clean business name for matching"""
        import re
        name = name.lower()
        name = re.sub(r'[^\w\s]', '', name)
        stopwords = ['dr', 'doctor', 'clinic', 'hospital', 'center', 'the', 'in', 'at', 'and', 'or']
        words = [w for w in name.split() if w not in stopwords]
        return ' '.join(words)
    
    def _create_error_result(self, keyword, location, business_name, error):
        return {
            'keyword': keyword,
            'location': location,
            'searched_business': business_name,
            'found_business_name': None,
            'position': None,
            'page': None,
            'found': False,
            'error': error,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _create_not_found_result(self, keyword, location, business_name, checked):
        return {
            'keyword': keyword,
            'location': location,
            'searched_business': business_name,
            'found_business_name': None,
            'position': None,
            'page': None,
            'found': False,
            'total_checked': checked,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def close(self):
        """✅ Complete resource cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except OSError as e:
                if "handle is invalid" not in str(e).lower():
                    try:
                        self.driver.close()
                    except:
                        pass
            except Exception:
                try:
                    self.driver.close()
                except:
                    pass
            finally:
                self.driver = None
                gc.collect()
