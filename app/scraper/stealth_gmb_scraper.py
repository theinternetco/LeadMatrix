"""
🔥🔥🔥 ULTIMATE GMB SCRAPER - V12.1 SMART OCR EXTRACTION 🔥🔥🔥
Version: 12.1 FINAL - October 2025 - SMART POSITION-AWARE OCR
Save this as: stealth_gmb_scraper.py
"""
import time
import random
import re
import json
import urllib.parse
from typing import Dict, Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc

# OCR imports
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
    print("✅ OCR support enabled (pytesseract)")
except ImportError:
    try:
        import easyocr
        OCR_AVAILABLE = True
        print("✅ OCR support enabled (easyocr)")
    except ImportError:
        OCR_AVAILABLE = False
        print("⚠️  OCR not available. Install: pip install pytesseract pillow OR pip install easyocr")


class StealthGMBScraper:
    """🔥 Ultimate GMB Scraper V12.1 - Smart Position-Aware OCR"""
    
    def __init__(self, mode: str = "auto", headless: bool = False, debug_port: int = 9222):
        self.mode = mode.lower()
        self.headless = headless
        self.debug_port = debug_port
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.businesses = []
        
        # Initialize EasyOCR if available
        if OCR_AVAILABLE:
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(['en'], gpu=False)
                self.ocr_method = 'easyocr'
                print("🔥 Using EasyOCR for text extraction")
            except:
                self.ocr_reader = None
                self.ocr_method = 'pytesseract'
                print("🔥 Using Pytesseract for text extraction")
        else:
            self.ocr_reader = None
            self.ocr_method = None
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        print("\n" + "="*70)
        print("🔥🔥🔥 GMB SCRAPER V12.1 - SMART OCR 🔥🔥🔥")
        print("="*70)
        print(f"   Mode: {'🤖 AUTO LOGIN' if self.mode == 'auto' else '🔗 MANUAL'}")
        print(f"   Method: Position-Aware Screenshot OCR")
        print(f"   OCR: {'✅ Enabled' if OCR_AVAILABLE else '❌ Disabled'}")
        print(f"   Incognito: Yes 🕵️")
        print("="*70 + "\n")
    
    def _initialize_stealth_driver(self):
        """🤖 Initialize INCOGNITO browser"""
        try:
            print("\n🔥 Initializing ultra-stealth INCOGNITO browser...")
            
            options = uc.ChromeOptions()
            options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--start-maximized")
            options.add_argument("--incognito")
            
            print("   ✅ Incognito mode enabled 🕵️")
            
            if self.headless:
                options.add_argument("--headless=new")
            
            # Anti-detection
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=IsolateOrigins,site-per-process")
            
            print("🌐 Starting Chrome...")
            self.driver = uc.Chrome(options=options, version_main=None)
            self.wait = WebDriverWait(self.driver, 30)
            
            self._inject_stealth_scripts()
            time.sleep(2)
            
            print("✅ Browser ready!\n")
            
        except Exception as e:
            print(f"❌ Browser init failed: {str(e)[:300]}")
            import traceback
            traceback.print_exc()
            raise
    
    def login(self, email: str, password: str):
        """🔐 Auto-login to GMB"""
        print(f"\n{'='*70}")
        print("🔐 LOGGING IN TO GMB")
        print(f"{'='*70}")
        print(f"📧 Email: {email}")
        print(f"{'='*70}\n")
        
        if not self.driver:
            self._initialize_stealth_driver()
        
        try:
            self.driver.delete_all_cookies()
            
            print("🌐 Opening Google Accounts...")
            self.driver.get("https://accounts.google.com/")
            time.sleep(random.uniform(4, 6))
            
            print("📧 Entering email...")
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.click()
            time.sleep(0.5)
            self._human_like_typing(email_input, email)
            time.sleep(random.uniform(1, 2))
            
            self.driver.find_element(By.ID, "identifierNext").click()
            time.sleep(random.uniform(4, 6))
            
            print("🔑 Entering password...")
            password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
            password_input.click()
            time.sleep(0.5)
            self._human_like_typing(password_input, password)
            time.sleep(random.uniform(1, 2))
            
            self.driver.find_element(By.ID, "passwordNext").click()
            print("⏳ Authenticating...")
            time.sleep(random.uniform(8, 12))
            
            try:
                self.driver.find_element(By.XPATH, "//*[contains(text(), 'verify') or contains(text(), 'Verify')]")
                print("\n⚠️ 2FA DETECTED! Complete in browser...")
                time.sleep(90)
            except:
                print("✅ No 2FA")
            
            print("🌐 Opening GMB...")
            self.driver.get("https://business.google.com/locations")
            time.sleep(random.uniform(8, 12))
            
            current_url = self.driver.current_url
            
            if "business.google.com" in current_url:
                print("\n" + "="*70)
                print("✅✅✅ LOGIN SUCCESSFUL ✅✅✅")
                print("="*70 + "\n")
                self.logged_in = True
                
                print("\n📋 Auto-fetching businesses...")
                self.list_all_businesses()
                
                return True
            else:
                print("\n❌ Login failed")
                return False
                
        except Exception as e:
            print(f"\n❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_all_businesses(self) -> List[Dict]:
        """📋 Extract ALL businesses"""
        if not self.logged_in:
            print("❌ Not logged in!")
            return []
        
        try:
            print(f"\n{'='*70}")
            print("📋 EXTRACTING BUSINESSES")
            print(f"{'='*70}\n")
            
            current_url = self.driver.current_url
            if "locations" not in current_url:
                print("🌐 Navigating...")
                self.driver.get("https://business.google.com/locations")
                time.sleep(10)
            
            print("⏳ Waiting for content...")
            
            for attempt in range(15):
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    if "businesses" in page_text.lower() or "business" in page_text.lower():
                        print(f"   ✅ Content loaded (attempt {attempt + 1})")
                        break
                except:
                    pass
                print(f"   ⏳ Waiting... ({attempt + 1}/15)")
                time.sleep(2)
            
            time.sleep(5)
            
            print("📜 Scrolling...")
            for i in range(10):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.5)
            
            time.sleep(3)
            
            print("📄 Extracting...")
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            page_source = self.driver.page_source
            
            try:
                with open("gmb_debug.html", "w", encoding="utf-8") as f:
                    f.write(page_source)
                with open("gmb_debug_text.txt", "w", encoding="utf-8") as f:
                    f.write(page_text)
                self.driver.save_screenshot("gmb_extraction.png")
                print("   💾 Debug files saved")
            except:
                pass
            
            count_match = re.search(r'(\d+)\s+business(?:es)?', page_text, re.IGNORECASE)
            expected_count = int(count_match.group(1)) if count_match else 0
            print(f"\n📊 Expected: {expected_count} businesses\n")
            
            businesses = []
            seen_names = set()
            
            print("🔍 Parsing...")
            
            lines = page_text.split('\n')
            print(f"   Analyzing {len(lines)} lines\n")
            
            for line in lines:
                line = line.strip()
                
                if len(line) < 10:
                    continue
                
                if 10 <= len(line) <= 150:
                    capitals = sum(1 for c in line if c.isupper())
                    if capitals < 2:
                        continue
                    
                    skip_words = [
                        'shop code', 'verified', 'unverified', 'create group', 
                        'add business', 'filter', 'sort', 'status', 'all (',
                        'see your profile', 'businesses', 'reviews', 'verifications',
                        'linked accounts', 'settings', 'support', 'google business',
                        'profile manager', 'search businesses'
                    ]
                    if any(skip_word in line.lower() for skip_word in skip_words):
                        continue
                    
                    if re.match(r'^[0-9\s\-\(\)]+$', line):
                        continue
                    
                    if line.count(',') > 3:
                        continue
                    
                    if 'http' in line.lower() or 'www.' in line.lower():
                        continue
                    
                    if line not in seen_names:
                        businesses.append({"id": len(businesses) + 1, "name": line})
                        seen_names.add(line)
                        print(f"   [{len(businesses)}] {line}")
                
                if len(businesses) >= expected_count * 1.5:
                    break
            
            print(f"\n   ✅ Extracted: {len(businesses)} raw\n")
            
            print("🧹 Cleaning...")
            businesses = self._clean_business_list(businesses)
            self.businesses = businesses
            
            print(f"{'='*70}")
            if len(businesses) > 0:
                print(f"✅✅✅ EXTRACTED {len(businesses)} BUSINESSES ✅✅✅")
                print(f"{'='*70}\n")
                
                for biz in businesses:
                    print(f"  [{biz['id']}] {biz['name']}")
                
                print(f"\n{'='*70}")
                percentage = (len(businesses) / expected_count * 100) if expected_count > 0 else 0
                print(f"📊 SUMMARY: {len(businesses)}/{expected_count} ({percentage:.1f}%)")
                print(f"{'='*70}\n")
            else:
                print("❌ NO BUSINESSES EXTRACTED")
                print(f"{'='*70}\n")
            
            return businesses
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _clean_business_list(self, businesses: List[Dict]) -> List[Dict]:
        """🧹 Clean and deduplicate"""
        cleaned = []
        seen = set()
        
        for biz in businesses:
            name = biz['name'].strip()
            
            # Remove shop codes
            name = re.sub(r'^\d{18,25}\s+', '', name)
            
            # Remove suffixes
            name = re.sub(r'\s+(See your profile|Verified|Unverified)$', '', name, flags=re.IGNORECASE)
            name = name.strip()
            
            if len(name) < 5 or len(name) > 200:
                continue
            
            skip_words = ['shop code', 'status', 'verified', 'create', 'add', 'filter', 
                         'sort', 'settings', 'businesses', 'profile', '©2025 google', 
                         'terms-privacy', 'content policy', 'privacy policy']
            if any(word in name.lower() for word in skip_words):
                continue
            
            if re.match(r'^\d{10,}', name):
                continue
            
            if re.match(r'^[0-9\-\s\(\)]+$', name):
                continue
            
            name_lower = name.lower()
            if name_lower in seen:
                continue
            
            seen.add(name_lower)
            cleaned.append({"id": len(cleaned) + 1, "name": name})
        
        print(f"   ✅ Cleaned: {len(businesses)} → {len(cleaned)}\n")
        return cleaned
    
    def scrape_all_performance_tabs(self) -> Dict:
        """📊 🔥 V12.1: Smart OCR-based extraction"""
        try:
            print(f"\n{'='*70}")
            print("📊 V12.1 SMART OCR EXTRACTION")
            print(f"{'='*70}\n")
            
            if not self.driver:
                return {"status": "error", "error": "Browser not initialized"}
            
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}\n")
            
            time.sleep(3)
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            
            has_performance_modal = "Business Profile interactions" in page_text or "customer interactions" in page_text
            has_performance_url = ("business.google.com" in current_url and ("/performance" in current_url or "/insights" in current_url))
            is_google_search_modal = "google.com/search" in current_url and has_performance_modal
            
            if not (has_performance_url or is_google_search_modal):
                print("❌❌❌ CRITICAL ERROR: NO PERFORMANCE DATA DETECTED! ❌❌❌\n")
                print("📋 INSTRUCTIONS:")
                print("="*70)
                print("Neither GMB Performance page NOR Google Search Performance modal detected!")
                print("\nPlease:")
                print("  1. Go to Google and search for your business")
                print("  2. Click the 'Performance' button")
                print("  3. Wait for the modal/popup to open with charts")
                print("  4. Then call the scraper API")
                print("="*70)
                
                return {
                    "status": "error",
                    "error": "No Performance data detected. Open Performance modal first.",
                    "current_url": current_url
                }
            
            if is_google_search_modal:
                print("✅ Google Search Performance MODAL detected!\n")
                print("⚠️  NOTE: This is a modal popup - URL won't change when clicking tabs\n")
            else:
                print("✅ GMB Performance page detected!\n")
            
            # Extract business name
            business_name = self._extract_business_name_from_performance()
            print(f"🏢 Business: {business_name}\n")
            
            if business_name == "Unknown Business":
                print("⚠️  Could not auto-detect business name\n")
                if "Business Profile interactions" in page_text:
                    lines = page_text.split('\n')
                    for i, line in enumerate(lines):
                        if "Business Profile interactions" in line or "customer interactions" in line:
                            for j in range(max(0, i-5), i):
                                potential_name = lines[j].strip()
                                if len(potential_name) > 5 and len(potential_name) < 100:
                                    if not any(word in potential_name.lower() for word in ['performance', 'google', 'accessibility']):
                                        business_name = potential_name
                                        print(f"   ✅ Found business name: {business_name}\n")
                                        break
                            break
            
            if business_name == "Unknown Business":
                business_name = input("👉 Please enter the business name manually: ").strip()
                if not business_name:
                    business_name = "Unknown Business"
            
            print(f"✅ Confirmed: {business_name}\n")
            
            tabs = [
                {"name": "Overview", "emoji": "📊", "key": "overview"},
                {"name": "Calls", "emoji": "📞", "key": "calls"},
                {"name": "Chat clicks", "emoji": "💬", "key": "chat_clicks"},
                {"name": "Bookings", "emoji": "📅", "key": "bookings"},
                {"name": "Directions", "emoji": "🗺️", "key": "directions"},
                {"name": "Website clicks", "emoji": "🌐", "key": "website_clicks"}
            ]
            
            all_data = {
                "business_name": business_name,
                "url": current_url,
                "scrape_type": "google_search_modal" if is_google_search_modal else "gmb_performance_page",
                "tabs": {},
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Tab 1: Overview
            print(f"{'='*70}")
            print(f"✅ TAB 1/6: {tabs[0]['emoji']} {tabs[0]['name'].upper()}")
            print(f"{'='*70}")
            print("⏳ Scraping Overview tab (current page)...")
            time.sleep(3)
            
            overview_data = self._scrape_tab_with_ocr(tabs[0]['name'])
            all_data["tabs"][tabs[0]["key"]] = overview_data
            
            print(f"✅ {tabs[0]['name']} scraped: {overview_data.get('primary_value', 'N/A')}")
            print(f"{'='*70}\n")
            
            # Tabs 2-6
            for i, tab in enumerate(tabs[1:], start=2):
                print(f"{'='*70}")
                print(f"🔄 TAB {i}/6: {tab['emoji']} {tab['name'].upper()}")
                print(f"{'='*70}")
                print(f"\n📍 ACTION REQUIRED IN BROWSER:")
                print(f"   1. Look for the '{tab['name']}' tab in the modal/page")
                print(f"   2. Click it")
                print(f"   3. Wait 2-3 seconds for data to load")
                print(f"   4. Then press ENTER here\n")
                
                input(f"👉 Press ENTER after clicking '{tab['name']}' tab...")
                
                print(f"⏳ Waiting for data to load...")
                time.sleep(5)
                
                print(f"📊 Scraping {tab['name']}...")
                tab_data = self._scrape_tab_with_ocr(tab['name'])
                all_data["tabs"][tab["key"]] = tab_data
                
                print(f"✅ {tab['name']} scraped: {tab_data.get('primary_value', 'N/A')}")
                print(f"{'='*70}\n")
            
            # Final summary
            print(f"\n{'='*70}")
            print("✅✅✅ ALL TABS SCRAPED SUCCESSFULLY! ✅✅✅")
            print(f"{'='*70}")
            print(f"🏢 Business: {business_name}")
            for tab in tabs:
                value = all_data['tabs'].get(tab['key'], {}).get('primary_value', 'N/A')
                print(f"{tab['emoji']} {tab['name']}: {value}")
            print(f"{'='*70}\n")
            
            return {"status": "success", "data": all_data}
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    def _extract_business_name_from_performance(self) -> str:
        """Extract business name specifically from Performance page"""
        try:
            current_url = self.driver.current_url
            if "/l/" in current_url:
                parts = current_url.split("/l/")[1].split("/")[0]
                decoded = urllib.parse.unquote(parts)
                if len(decoded) > 5 and not decoded.isdigit():
                    return decoded
            
            title = self.driver.title
            if title and " - " in title:
                name = title.split(" - ")[0].strip()
                if len(name) > 3 and name.lower() not in ['performance', 'insights', 'businesses']:
                    return name
            
            try:
                js_script = """
                let candidates = [];
                document.querySelectorAll('h1, h2, [role="heading"]').forEach(el => {
                    let text = el.textContent.trim();
                    if (text.length > 3 && text.length < 100) {
                        let lower = text.toLowerCase();
                        if (!lower.includes('performance') && 
                            !lower.includes('insights') && 
                            !lower.includes('dashboard') &&
                            !lower.includes('businesses') &&
                            !lower.includes('accessibility')) {
                            candidates.push(text);
                        }
                    }
                });
                return candidates[0] || '';
                """
                name = self.driver.execute_script(js_script)
                if name and len(name) > 3:
                    return name
            except:
                pass
            
            return self._extract_business_name()
            
        except:
            return "Unknown Business"
    
    def _scrape_tab_with_ocr(self, tab_name: str) -> Dict:
        """📸 🔥 V12.1: SMART POSITION-AWARE OCR"""
        try:
            screenshot_path = f"tab_{tab_name.lower().replace(' ', '_')}_{int(time.time())}.png"
            
            print(f"   ⏳ Waiting 5 seconds for '{tab_name}' content...")
            time.sleep(5)
            
            # Take screenshot
            self.driver.save_screenshot(screenshot_path)
            print(f"   📸 Screenshot saved: {screenshot_path}")
            
            if not OCR_AVAILABLE:
                print(f"   ⚠️  OCR not available! Returning 0")
                return {
                    "primary_value": 0,
                    "extraction_method": "V12.1 - OCR Disabled",
                    "error": "OCR libraries not installed"
                }
            
            print(f"   🔍 Running Smart OCR on screenshot...")
            
            # Extract text with POSITION information (for EasyOCR)
            if self.ocr_method == 'easyocr' and self.ocr_reader:
                # EasyOCR returns: [(bbox, text, confidence)]
                result = self.ocr_reader.readtext(screenshot_path)
                
                extracted_text = ' '.join([item[1] for item in result])
                print(f"   📄 OCR extracted {len(extracted_text)} characters")
                
                # Find numbers with their positions
                number_candidates = []
                for item in result:
                    bbox, text, confidence = item
                    text = text.strip()
                    
                    # Check if it's a number
                    if re.match(r'^\d{1,5}$', text):
                        num = int(text)
                        
                        # Get Y position (top of bounding box)
                        y_position = bbox[0][1]  # Top-left Y coordinate
                        
                        # Get font size estimate (height of bounding box)
                        box_height = abs(bbox[2][1] - bbox[0][1])
                        
                        number_candidates.append({
                            'number': num,
                            'y_position': y_position,
                            'box_height': box_height,
                            'confidence': confidence,
                            'text': text
                        })
                
                print(f"   🔢 Found {len(number_candidates)} number candidates")
                
                if number_candidates:
                    # Sort by: 1) Y position (top first), 2) Box height (largest first)
                    number_candidates.sort(key=lambda x: (x['y_position'], -x['box_height']))
                    
                    print(f"\n   📋 Top 5 Number Candidates:")
                    for i, item in enumerate(number_candidates[:5], 1):
                        print(f"      #{i}: {item['number']} | Y:{item['y_position']:.0f} | Height:{item['box_height']:.0f}px | Conf:{item['confidence']:.2f}")
                    
                    # Filter valid numbers (exclude chart scale numbers)
                    valid_numbers = [
                        c for c in number_candidates 
                        if 0 <= c['number'] <= 50000 and 
                           not (2020 <= c['number'] <= 2030) and
                           c['number'] not in [240, 180, 120, 60, 30, 15, 5]  # Common chart scales
                    ]
                    
                    if valid_numbers:
                        # Find the number with the LARGEST box height in the TOP area
                        # (Top area = first 30% of image height)
                        top_area_threshold = min([c['y_position'] for c in valid_numbers]) + 300  # Top 300px
                        
                        top_numbers = [c for c in valid_numbers if c['y_position'] < top_area_threshold]
                        
                        if top_numbers:
                            # Get the largest (by height) number in top area
                            top_numbers.sort(key=lambda x: -x['box_height'])
                            primary_value = top_numbers[0]['number']
                            
                            print(f"\n   ✅ Smart OCR Match: {primary_value}")
                            print(f"       Position: Y={top_numbers[0]['y_position']:.0f}")
                            print(f"       Height: {top_numbers[0]['box_height']:.0f}px")
                            print(f"   🎯 FINAL Primary value: {primary_value}\n")
                            
                            return {
                                "primary_value": primary_value,
                                "extraction_method": "V12.1 - Smart OCR (EasyOCR)",
                                "all_numbers_found": [c['number'] for c in valid_numbers[:10]],
                                "screenshot": screenshot_path,
                                "confidence": top_numbers[0]['confidence']
                            }
                        else:
                            # No numbers in top area, use first valid
                            primary_value = valid_numbers[0]['number']
                            print(f"\n   ⚠️  Fallback: Using first valid number: {primary_value}\n")
                            
                            return {
                                "primary_value": primary_value,
                                "extraction_method": "V12.1 - OCR Fallback",
                                "screenshot": screenshot_path
                            }
            else:
                # Pytesseract fallback (no position info)
                from PIL import Image
                import pytesseract
                
                img = Image.open(screenshot_path)
                extracted_text = pytesseract.image_to_string(img)
                
                print(f"   📄 OCR extracted {len(extracted_text)} characters")
                
                # Find all numbers
                numbers = re.findall(r'\b(\d{1,5})\b', extracted_text)
                print(f"   🔢 Found {len(numbers)} numbers in OCR text")
                
                if numbers:
                    # Filter valid numbers
                    valid_numbers = []
                    for num_str in numbers:
                        num = int(num_str)
                        if 0 <= num <= 50000 and not (2020 <= num <= 2030) and num not in [240, 180, 120, 60, 30, 15, 5]:
                            valid_numbers.append(num)
                    
                    print(f"   ✅ Valid numbers: {valid_numbers[:10]}")
                    
                    if valid_numbers:
                        # Return the FIRST valid number
                        primary_value = valid_numbers[0]
                        
                        print(f"\n   ✅ OCR Match: {primary_value}")
                        print(f"   🎯 FINAL Primary value: {primary_value}\n")
                        
                        return {
                            "primary_value": primary_value,
                            "extraction_method": "V12.1 - OCR (Pytesseract)",
                            "all_numbers_found": valid_numbers[:20],
                            "screenshot": screenshot_path
                        }
            
            print(f"\n   ❌ NO VALID NUMBER FOUND IN OCR!")
            print(f"   🎯 FINAL Primary value: 0\n")
            
            return {
                "primary_value": 0,
                "extraction_method": "V12.1 - OCR No Match",
                "screenshot": screenshot_path
            }
            
        except Exception as e:
            print(f"⚠️  OCR Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "primary_value": 0,
                "error": str(e),
                "screenshot": screenshot_path
            }
    
    def scrape_current_page_performance(self) -> Dict:
        """📊 Scrape performance data from current page"""
        try:
            print(f"\n{'='*70}")
            print("📊 EXTRACTING PERFORMANCE")
            print(f"{'='*70}\n")
            
            if not self.driver:
                raise Exception("Browser not connected!")
            
            current_url = self.driver.current_url
            print(f"📍 URL: {current_url}\n")
            
            time.sleep(3)
            
            try:
                self.driver.save_screenshot("performance_data.png")
                print("📸 Screenshot saved")
            except:
                pass
            
            business_name = self._extract_business_name()
            print(f"🏢 Business: {business_name}\n")
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
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
            
            print("\n" + "="*70)
            print("✅ EXTRACTED!")
            print("="*70)
            print(f"🏢 {metrics['business_name']}")
            print(f"📊 Interactions: {metrics['total_interactions']}")
            print(f"📞 Calls: {metrics['calls']}")
            print(f"🗺️  Directions: {metrics['directions']}")
            print(f"🌐 Website: {metrics['website_clicks']}")
            print("="*70 + "\n")
            
            return {"status": "success", "data": metrics}
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _inject_stealth_scripts(self):
        """💉 Inject anti-detection scripts"""
        scripts = [
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});",
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});",
            "window.chrome = {runtime: {}};",
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
            for selector in ["h1", "[role='heading']", "h2"]:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = elem.text.strip()
                    if name and len(name) > 3:
                        if name.lower() not in ['performance', 'insights', 'dashboard', 'accessibility links']:
                            return name
                except:
                    continue
            return "Unknown Business"
        except:
            return "Unknown Business"
    
    def _extract_interactions(self, text: str) -> int:
        """Extract total interactions"""
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
        """Find specific metric in text"""
        try:
            text_lower = text.lower()
            for keyword in keywords:
                patterns = [rf'(\d{{1,5}})\s*{keyword}', rf'{keyword}\s*(\d{{1,5}})']
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
        """Get current URL"""
        try:
            return self.driver.current_url if self.driver else ""
        except:
            return ""
    
    def close(self):
        """Close browser"""
        if self.driver:
            try:
                print("\n👋 Closing...")
                self.driver.quit()
                print("✅ Closed\n")
            except:
                pass


def interactive_mode():
    """🎯 Interactive mode for standalone use"""
    print("\n" + "="*70)
    print("🔥 GMB SCRAPER V12.1 - INTERACTIVE MODE")
    print("="*70 + "\n")
    
    email = input("📧 Gmail: ").strip()
    password = input("🔑 Password: ").strip()
    
    scraper = StealthGMBScraper(mode="auto", headless=False)
    
    try:
        if scraper.login(email, password):
            print("\n✅ Login successful! Browser is ready for scraping.")
        else:
            print("❌ Login failed!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted!")
    finally:
        scraper.close()


if __name__ == "__main__":
    interactive_mode()
