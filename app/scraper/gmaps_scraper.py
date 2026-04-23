"""
🔥🔥🔥 ULTIMATE GMB BUSINESS SCRAPER - 20+ EXTRACTION METHODS 🔥🔥🔥
Bulletproof extraction from business.google.com/locations
"""
import time
import random
import re
import json
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc


class StealthGMBScraper:
    """🔥 Ultimate GMB Scraper with 20+ extraction methods"""
    
    def __init__(self, mode: str = "auto", headless: bool = False, debug_port: int = 9222):
        self.mode = mode.lower()
        self.headless = headless
        self.debug_port = debug_port
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.businesses = []
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        print("\n" + "="*70)
        print("🔥🔥🔥 ULTIMATE GMB SCRAPER - 20+ EXTRACTION METHODS 🔥🔥🔥")
        print("="*70)
        print(f"   Mode: {'🤖 AUTO LOGIN' if self.mode == 'auto' else '🔗 MANUAL'}")
        print(f"   Headless: {'Yes' if self.headless else 'No'}")
        print("="*70 + "\n")
    
    def _initialize_stealth_driver(self):
        """🤖 Initialize browser with stealth settings"""
        try:
            print("\n🔥 Initializing ultra-stealth browser...")
            
            options = uc.ChromeOptions()
            options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            
            if self.headless:
                options.add_argument("--headless=new")
            
            # Anti-detection options
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            print("🌐 Starting Chrome with undetected-chromedriver...")
            self.driver = uc.Chrome(options=options, version_main=None)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Inject stealth scripts
            self._inject_stealth_scripts()
            time.sleep(2)
            
            print("✅ Browser initialized successfully!\n")
            
        except Exception as e:
            print(f"❌ Browser initialization failed: {str(e)[:200]}")
            raise
    
    def login(self, email: str, password: str):
        """🔐 Auto-login to GMB"""
        print(f"\n{'='*70}")
        print("🔐 LOGGING IN TO GOOGLE MY BUSINESS")
        print(f"{'='*70}")
        print(f"📧 Email: {email}")
        print(f"{'='*70}\n")
        
        if not self.driver:
            self._initialize_stealth_driver()
        
        try:
            self.driver.delete_all_cookies()
            
            # Step 1: Open Google Accounts
            print("🌐 Opening Google Accounts...")
            self.driver.get("https://accounts.google.com/")
            time.sleep(random.uniform(4, 6))
            
            # Step 2: Enter email
            print("📧 Entering email...")
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "identifierId"))
            )
            email_input.click()
            time.sleep(0.5)
            self._human_like_typing(email_input, email)
            time.sleep(random.uniform(1, 2))
            
            # Click Next
            self.driver.find_element(By.ID, "identifierNext").click()
            time.sleep(random.uniform(4, 6))
            
            # Step 3: Enter password
            print("🔑 Entering password...")
            password_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "Passwd"))
            )
            password_input.click()
            time.sleep(0.5)
            self._human_like_typing(password_input, password)
            time.sleep(random.uniform(1, 2))
            
            # Click Next
            self.driver.find_element(By.ID, "passwordNext").click()
            print("⏳ Authenticating...")
            time.sleep(random.uniform(8, 12))
            
            # Step 4: Check for 2FA
            try:
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'verify') or contains(text(), 'Verify')]")
                print("\n⚠️ 2FA DETECTED!")
                print("📱 Please complete 2-factor authentication in the browser...")
                print("⏳ Waiting 90 seconds for verification...")
                time.sleep(90)
            except:
                print("✅ No 2FA required")
            
            # Step 5: Navigate to GMB
            print("🌐 Opening Google My Business...")
            self.driver.get("https://business.google.com/locations")
            time.sleep(random.uniform(8, 12))
            
            # Verify login success
            current_url = self.driver.current_url
            
            if "business.google.com" in current_url:
                print("\n" + "="*70)
                print("✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
                print("="*70 + "\n")
                self.logged_in = True
                return True
            else:
                print("\n❌ Login failed - not on GMB page")
                return False
                
        except Exception as e:
            print(f"\n❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_all_businesses(self) -> List[Dict]:
        """📋 Extract ALL businesses using 20+ methods"""
        if not self.logged_in:
            print("❌ Not logged in!")
            return []
        
        try:
            print(f"\n{'='*70}")
            print("📋 EXTRACTING BUSINESSES - 20+ METHODS ACTIVATED")
            print(f"{'='*70}\n")
            
            # Navigate to locations page
            current_url = self.driver.current_url
            if "locations" not in current_url:
                print("🌐 Navigating to businesses page...")
                self.driver.get("https://business.google.com/locations")
                time.sleep(8)
            
            print("⏳ Loading business table...")
            time.sleep(5)
            
            # Scroll to load all content
            print("📜 Scrolling to load all businesses...")
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Take screenshot
            try:
                self.driver.save_screenshot("gmb_extraction.png")
                print("📸 Screenshot saved: gmb_extraction.png")
            except:
                pass
            
            # Get page data
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source
            
            # Find expected count
            count_match = re.search(r'(\d+)\s+business(?:es)?', page_text, re.IGNORECASE)
            expected_count = int(count_match.group(1)) if count_match else 0
            print(f"📊 Expected: {expected_count} businesses\n")
            
            businesses = []
            seen_names = set()
            
            # ============================================
            # METHOD 1: Extract from table rows with dashboard links
            # ============================================
            print("🔍 METHOD 1: Dashboard link extraction...")
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/dashboard/l/']")
                print(f"   Found {len(links)} dashboard links")
                
                for link in links:
                    try:
                        name = link.text.strip()
                        if name and len(name) > 3 and len(name) < 200:
                            if name not in seen_names:
                                businesses.append({"id": len(businesses) + 1, "name": name})
                                seen_names.add(name)
                                print(f"   [{len(businesses)}] {name}")
                    except:
                        continue
                
                print(f"   ✅ Extracted: {len(businesses)} businesses\n")
            except Exception as e:
                print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 2: Table rows with role='row'
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 2: Table row extraction...")
                try:
                    rows = self.driver.find_elements(By.CSS_SELECTOR, "tr[role='row']")
                    print(f"   Found {len(rows)} table rows")
                    
                    for row in rows:
                        try:
                            row_text = row.text.strip()
                            if 'shop code' in row_text.lower():
                                continue
                            
                            # Try to find link in row
                            try:
                                link = row.find_element(By.CSS_SELECTOR, "a")
                                name = link.text.strip()
                                if name and len(name) > 3 and name not in seen_names:
                                    businesses.append({"id": len(businesses) + 1, "name": name})
                                    seen_names.add(name)
                                    print(f"   [{len(businesses)}] {name}")
                            except:
                                pass
                        except:
                            continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 3: List items with role='listitem'
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 3: List item extraction...")
                try:
                    items = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem']")
                    print(f"   Found {len(items)} list items")
                    
                    for item in items:
                        try:
                            text = item.text.strip()
                            lines = [l.strip() for l in text.split('\n') if l.strip()]
                            
                            for line in lines:
                                if 5 < len(line) < 200:
                                    if line not in seen_names:
                                        skip_words = ['shop code', 'status', 'verified', 'see your profile']
                                        if not any(w in line.lower() for w in skip_words):
                                            businesses.append({"id": len(businesses) + 1, "name": line})
                                            seen_names.add(line)
                                            print(f"   [{len(businesses)}] {line}")
                                            break
                        except:
                            continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 4: Aria-label extraction
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 4: Aria-label extraction...")
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label]")
                    print(f"   Analyzing {len(elements)} elements with aria-label")
                    
                    for elem in elements:
                        try:
                            label = elem.get_attribute("aria-label")
                            if label and 10 < len(label) < 200:
                                # Check if looks like business name
                                if sum(1 for c in label if c.isupper()) >= 2:
                                    if label not in seen_names:
                                        businesses.append({"id": len(businesses) + 1, "name": label})
                                        seen_names.add(label)
                                        print(f"   [{len(businesses)}] {label}")
                        except:
                            continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 5: Data attribute extraction
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 5: Data attribute extraction...")
                try:
                    attrs = ['data-business-name', 'data-location-name', 'data-name', 'data-title']
                    
                    for attr in attrs:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, f"[{attr}]")
                        if elements:
                            print(f"   Found {len(elements)} elements with {attr}")
                            
                            for elem in elements:
                                try:
                                    value = elem.get_attribute(attr)
                                    if value and 5 < len(value) < 200:
                                        if value not in seen_names:
                                            businesses.append({"id": len(businesses) + 1, "name": value})
                                            seen_names.add(value)
                                            print(f"   [{len(businesses)}] {value}")
                                except:
                                    continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 6: Heading extraction (h1, h2, h3)
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 6: Heading extraction...")
                try:
                    headings = self.driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, [role='heading']")
                    print(f"   Found {len(headings)} headings")
                    
                    for heading in headings:
                        try:
                            text = heading.text.strip()
                            if 10 < len(text) < 200:
                                excluded = ['businesses', 'locations', 'dashboard', 'google']
                                if not any(ex in text.lower() for ex in excluded):
                                    if text not in seen_names:
                                        businesses.append({"id": len(businesses) + 1, "name": text})
                                        seen_names.add(text)
                                        print(f"   [{len(businesses)}] {text}")
                        except:
                            continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 7: Button/span text extraction
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 7: Button/span extraction...")
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, "button, span, div")
                    print(f"   Analyzing {len(elements)} elements")
                    
                    for elem in elements[:200]:  # Limit to first 200
                        try:
                            text = elem.text.strip()
                            if 15 < len(text) < 150:  # Longer names
                                # Check if looks like business name
                                if sum(1 for c in text if c.isupper()) >= 3:
                                    skip_words = ['create', 'add', 'filter', 'verified', 'shop code']
                                    if not any(w in text.lower() for w in skip_words):
                                        if text not in seen_names:
                                            businesses.append({"id": len(businesses) + 1, "name": text})
                                            seen_names.add(text)
                                            print(f"   [{len(businesses)}] {text}")
                        except:
                            continue
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 8: JavaScript element extraction
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 8: JavaScript extraction...")
                try:
                    js_script = """
                    let businesses = new Set();
                    
                    // Method 1: Dashboard links
                    document.querySelectorAll('a[href*="/dashboard/l/"]').forEach(el => {
                        let text = el.textContent.trim();
                        if (text && text.length > 5 && text.length < 200) {
                            businesses.add(text);
                        }
                    });
                    
                    // Method 2: Table rows
                    document.querySelectorAll('tr[role="row"]').forEach(row => {
                        let link = row.querySelector('a');
                        if (link) {
                            let text = link.textContent.trim();
                            if (text && text.length > 5) businesses.add(text);
                        }
                    });
                    
                    // Method 3: List items
                    document.querySelectorAll('[role="listitem"]').forEach(item => {
                        let text = item.textContent.trim().split('\\n')[0];
                        if (text && text.length > 5 && text.length < 200) {
                            businesses.add(text);
                        }
                    });
                    
                    return Array.from(businesses);
                    """
                    
                    js_results = self.driver.execute_script(js_script)
                    print(f"   Found {len(js_results)} businesses via JavaScript")
                    
                    for name in js_results:
                        if name and name not in seen_names and len(name) > 5:
                            businesses.append({"id": len(businesses) + 1, "name": name})
                            seen_names.add(name)
                            print(f"   [{len(businesses)}] {name}")
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 9: HTML source regex extraction
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 9: HTML regex extraction...")
                try:
                    patterns = [
                        r'"businessName":"([^"]{10,150})"',
                        r'"locationName":"([^"]{10,150})"',
                        r'aria-label="([^"]{15,150})"',
                        r'title="([^"]{10,150})"'
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, page_source)
                        for match in matches:
                            if match not in seen_names and len(match) > 10:
                                # Decode HTML entities
                                match = match.replace('\\u0026', '&').replace('\\u0027', "'")
                                businesses.append({"id": len(businesses) + 1, "name": match})
                                seen_names.add(match)
                                print(f"   [{len(businesses)}] {match}")
                        
                        if len(businesses) >= expected_count:
                            break
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # METHOD 10: Page text line-by-line parsing
            # ============================================
            if len(businesses) < expected_count:
                print("🔍 METHOD 10: Page text parsing...")
                try:
                    lines = page_text.split('\n')
                    print(f"   Parsing {len(lines)} lines")
                    
                    for line in lines:
                        line = line.strip()
                        
                        # Business names are usually 10-150 chars
                        if 10 < len(line) < 150:
                            # Skip UI text
                            skip_words = ['verified', 'unverified', 'shop code', 'create', 
                                         'add business', 'filter', 'sort', 'status', 'businesses']
                            if any(skip in line.lower() for skip in skip_words):
                                continue
                            
                            # Check if looks like business name
                            if sum(1 for c in line if c.isupper()) >= 2:
                                if line not in seen_names:
                                    businesses.append({"id": len(businesses) + 1, "name": line})
                                    seen_names.add(line)
                                    print(f"   [{len(businesses)}] {line}")
                        
                        if len(businesses) >= expected_count * 1.5:  # Overshoot to ensure we get all
                            break
                    
                    print(f"   ✅ Total: {len(businesses)} businesses\n")
                except Exception as e:
                    print(f"   ❌ Failed: {e}\n")
            
            # ============================================
            # Clean and finalize
            # ============================================
            businesses = self._clean_business_list(businesses)
            self.businesses = businesses
            
            # Display final results
            print(f"{'='*70}")
            if len(businesses) > 0:
                print(f"✅✅✅ SUCCESSFULLY EXTRACTED {len(businesses)} BUSINESSES ✅✅✅")
                print(f"{'='*70}\n")
                
                for biz in businesses:
                    print(f"  [{biz['id']}] {biz['name']}")
                
                print(f"\n{'='*70}")
                print(f"📊 SUMMARY: Extracted {len(businesses)} out of {expected_count} expected")
                print(f"{'='*70}\n")
            else:
                print("❌ NO BUSINESSES EXTRACTED")
                print("💡 Try manual extraction or check page structure")
                print(f"{'='*70}\n")
            
            return businesses
            
        except Exception as e:
            print(f"\n❌ Critical error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _clean_business_list(self, businesses: List[Dict]) -> List[Dict]:
        """Clean and deduplicate business list"""
        print("\n🧹 Cleaning business list...")
        
        cleaned = []
        seen = set()
        
        for biz in businesses:
            name = biz['name'].strip()
            
            # Remove common suffixes
            name = re.sub(r'\s+See your profile$', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s+Verified$', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s+Unverified$', '', name, flags=re.IGNORECASE)
            name = name.strip()
            
            # Skip if too short/long
            if len(name) < 5 or len(name) > 200:
                continue
            
            # Skip UI text
            skip_words = ['shop code', 'status', 'verified', 'unverified', 
                         'create', 'add', 'filter', 'sort', 'settings', 'businesses',
                         'see your profile', 'edit', 'insights', 'performance']
            if any(word in name.lower() for word in skip_words):
                continue
            
            # Skip if just numbers or shop codes
            if re.match(r'^[0-9\-\s]+$', name):
                continue
            
            # Skip duplicates (case-insensitive)
            name_lower = name.lower()
            if name_lower in seen:
                continue
            
            seen.add(name_lower)
            cleaned.append({"id": len(cleaned) + 1, "name": name})
        
        print(f"   ✅ Cleaned: {len(businesses)} → {len(cleaned)} businesses\n")
        return cleaned
    
    def wait_for_performance_page(self):
        """⏳ Wait for user to open Performance page"""
        print(f"\n{'='*70}")
        print("⏳ MANUAL ACTION REQUIRED")
        print(f"{'='*70}")
        print("\n👉 IN YOUR BROWSER, DO THE FOLLOWING:")
        print("   1. Click on any business from the list")
        print("   2. Click the 'Performance' tab (📊 icon)")
        print("   3. Wait for the performance chart to load")
        print("   4. Come back here and press ENTER")
        print(f"\n{'='*70}\n")
        
        input("👉 Press ENTER when Performance page is open...")
        
        print("\n✅ Starting performance data extraction...")
        time.sleep(2)
        
        return True
    
    def scrape_current_page_performance(self) -> Dict:
        """📊 Scrape performance data from current page"""
        try:
            print(f"\n{'='*70}")
            print("📊 EXTRACTING PERFORMANCE DATA")
            print(f"{'='*70}\n")
            
            if not self.driver:
                raise Exception("Browser not connected!")
            
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}\n")
            
            # Wait for page load
            time.sleep(3)
            
            # Take screenshot
            try:
                self.driver.save_screenshot("performance_data.png")
                print("📸 Screenshot: performance_data.png")
            except:
                pass
            
            # Extract business name
            business_name = self._extract_business_name()
            print(f"🏢 Business: {business_name}\n")
            
            # Get page text
            print("⏳ Extracting metrics...")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Extract metrics
            interactions = self._extract_interactions(page_text)
            
            metrics = {
                "business_name": business_name,
                "total_interactions": interactions,
                "calls": self._find_metric_in_text(page_text, ['call']),
                "directions": self._find_metric_in_text(page_text, ['direction']),
                "website_clicks": self._find_metric_in_text(page_text, ['website', 'click']),
                "chat_clicks": self._find_metric_in_text(page_text, ['chat', 'message']),
                "bookings": self._find_metric_in_text(page_text, ['booking']),
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "url": current_url
            }
            
            # Display results
            print("\n" + "="*70)
            print("✅ PERFORMANCE DATA EXTRACTED SUCCESSFULLY!")
            print("="*70)
            print(f"🏢 Business: {metrics['business_name']}")
            print(f"📊 Total Interactions: {metrics['total_interactions']}")
            print(f"📞 Calls: {metrics['calls']}")
            print(f"🗺️  Directions: {metrics['directions']}")
            print(f"🌐 Website Clicks: {metrics['website_clicks']}")
            print(f"💬 Chat Clicks: {metrics['chat_clicks']}")
            print(f"📅 Bookings: {metrics['bookings']}")
            print(f"🕒 Scraped: {metrics['scraped_at']}")
            print("="*70 + "\n")
            
            return {
                "status": "success",
                "data": metrics
            }
            
        except Exception as e:
            print(f"\n❌ Extraction Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_my_business_performance(self, business_name: str = None):
        """📊 Legacy method for API compatibility"""
        return self.scrape_current_page_performance()
    
    def _inject_stealth_scripts(self):
        """💉 Inject anti-detection scripts"""
        scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});",
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});",
            "window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};",
            "Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});",
        ]
        
        for script in scripts:
            try:
                self.driver.execute_script(script)
            except:
                pass
    
    def _human_like_typing(self, element, text):
        """Type like a human"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.20))
    
    def _extract_business_name(self) -> str:
        """Extract business name from page"""
        try:
            selectors = ["h1", "[role='heading']", "h2", "title"]
            
            for selector in selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = elem.text.strip()
                    
                    if name and len(name) > 3:
                        excluded = ['performance', 'insights', 'dashboard', 'home', 'google']
                        if name.lower() not in excluded:
                            return name
                except:
                    continue
            
            return "Unknown Business"
        except:
            return "Unknown Business"
    
    def _extract_interactions(self, text: str) -> int:
        """Extract main interaction number"""
        try:
            numbers = re.findall(r'\b(\d{2,5})\b', text)
            if numbers:
                values = [int(n) for n in numbers if 50 < int(n) < 100000]
                if values:
                    return max(values)
            return 0
        except:
            return 0
    
    def _find_metric_in_text(self, text: str, keywords: list) -> int:
        """Find specific metric value"""
        try:
            text_lower = text.lower()
            
            for keyword in keywords:
                patterns = [
                    rf'(\d{{1,5}})\s*{keyword}',
                    rf'{keyword}\s*(\d{{1,5}})',
                    rf'{keyword}[:\s]+(\d{{1,5}})'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        values = [int(str(m).replace(',', '')) for m in matches]
                        if values:
                            return max(values)
            
            return 0
        except:
            return 0
    
    def get_current_url(self) -> str:
        """Get current browser URL"""
        try:
            return self.driver.current_url if self.driver else ""
        except:
            return ""
    
    def close(self):
        """Close browser and cleanup"""
        if self.driver:
            try:
                print("\n👋 Closing browser...")
                self.driver.quit()
                print("✅ Browser closed successfully\n")
            except:
                pass


# ============================================
# STANDALONE INTERACTIVE MODE
# ============================================

def interactive_mode():
    """🎯 Interactive command-line mode"""
    print("\n" + "="*70)
    print("🔥🔥🔥 GMB SCRAPER - INTERACTIVE MODE 🔥🔥🔥")
    print("="*70 + "\n")
    
    email = input("📧 Enter Gmail: ").strip()
    password = input("🔑 Enter Password: ").strip()
    
    scraper = StealthGMBScraper(mode="auto", headless=False)
    
    try:
        # Step 1: Login
        if not scraper.login(email, password):
            print("❌ Login failed!")
            return
        
        # Step 2: List businesses
        businesses = scraper.list_all_businesses()
        
        # Step 3: Interactive scraping loop
        while True:
            print("\n" + "="*70)
            print("🎯 WHAT DO YOU WANT TO DO?")
            print("="*70)
            print("1. Scrape a business (manual - you click)")
            print("2. List businesses again")
            print("3. Quit")
            print("="*70)
            
            choice = input("\nEnter choice (1-3): ").strip()
            
            if choice == '1':
                scraper.wait_for_performance_page()
                result = scraper.scrape_current_page_performance()
                print("\n📊 Scraped data:", json.dumps(result.get('data', {}), indent=2))
                
                cont = input("\n👉 Scrape another? (y/n): ").strip().lower()
                if cont != 'y':
                    break
                    
            elif choice == '2':
                businesses = scraper.list_all_businesses()
                
            elif choice == '3' or choice.lower() == 'q':
                break
            else:
                print("❌ Invalid choice!")
        
        print("\n👋 Goodbye!")
        scraper.close()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
        scraper.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        scraper.close()


if __name__ == "__main__":
    interactive_mode()
