"""
🌍 MULTI-LOCATION SCRAPER - Get 1000+ Businesses
Automatically searches multiple areas to bypass 120-result limit
"""
import sys
import time
import json
import csv
import re
import random
import requests
from bs4 import BeautifulSoup
sys.path.insert(0, '.')

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

print("=" * 80)
print("🌍 MULTI-LOCATION SCRAPER - UNLIMITED RESULTS")
print("=" * 80)

# CONFIGURATION
business_type = input("\n📍 Business Type (e.g., 'digital marketing agency'): ").strip()
main_city = input("🌍 Main City (e.g., 'Mumbai'): ").strip()
target_per_search = int(input("📊 Results per search (max 120): ").strip() or "100")

# LOCATION DATABASE - Auto-generates search variations
MUMBAI_AREAS = [
    "Andheri", "Bandra", "Powai", "BKC", "Worli", "Lower Parel", 
    "Malad", "Goregaon", "Kandivali", "Borivali", "Dadar", "Kurla",
    "Chembur", "Ghatkopar", "Vikhroli", "Mulund", "Thane", "Navi Mumbai",
    "Juhu", "Versova", "Lokhandwala", "Santacruz", "Vile Parle"
]

DELHI_AREAS = [
    "Connaught Place", "Nehru Place", "Saket", "Dwarka", "Rohini",
    "Pitampura", "Janakpuri", "Laxmi Nagar", "Mayur Vihar", "Noida",
    "Gurgaon", "Greater Noida", "Faridabad", "South Extension"
]

BANGALORE_AREAS = [
    "Koramangala", "Indiranagar", "Whitefield", "Electronic City", "HSR Layout",
    "Marathahalli", "BTM Layout", "Jayanagar", "JP Nagar", "Malleshwaram",
    "Yelahanka", "Hebbal", "Sarjapur Road", "MG Road"
]

PUNE_AREAS = [
    "Kharadi", "Hinjewadi", "Viman Nagar", "Aundh", "Baner", "Wakad",
    "Magarpatta", "Hadapsar", "Shivaji Nagar", "Koregaon Park"
]

HYDERABAD_AREAS = [
    "Hitech City", "Gachibowli", "Madhapur", "Banjara Hills", "Jubilee Hills",
    "Kondapur", "Kukatpally", "Miyapur", "Secunderabad", "Ameerpet"
]

# Auto-select areas based on city
if "mumbai" in main_city.lower():
    areas = MUMBAI_AREAS
elif "delhi" in main_city.lower():
    areas = DELHI_AREAS
elif "bangalore" in main_city.lower() or "bengaluru" in main_city.lower():
    areas = BANGALORE_AREAS
elif "pune" in main_city.lower():
    areas = PUNE_AREAS
elif "hyderabad" in main_city.lower():
    areas = HYDERABAD_AREAS
else:
    # Generic areas for other cities
    areas = ["North", "South", "East", "West", "Central", "Downtown"]

# Generate search queries
search_queries = []

# Strategy 1: Location-based
for area in areas[:15]:  # Limit to 15 areas
    search_queries.append(f"{business_type} {area} {main_city}")

# Strategy 2: Keyword variations (if less than 10 areas)
if len(search_queries) < 10:
    variations = [
        f"{business_type} {main_city}",
        f"{business_type} near me {main_city}",
        f"best {business_type} {main_city}",
        f"top {business_type} {main_city}",
        f"{business_type} services {main_city}",
    ]
    search_queries.extend(variations)

print(f"\n⚙️ Configuration:")
print(f"   Business Type: {business_type}")
print(f"   City: {main_city}")
print(f"   Search Variations: {len(search_queries)}")
print(f"   Target per search: {target_per_search}")
print(f"   Maximum total: {len(search_queries) * target_per_search}")

print(f"\n📍 Will search these areas:")
for i, query in enumerate(search_queries, 1):
    print(f"   {i}. {query}")

confirm = input("\n✅ Start scraping? (y/n): ").lower()
if confirm != 'y':
    sys.exit(0)

def create_stealth_driver():
    """Create undetectable browser"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0"
    ]
    ua = random.choice(user_agents)
    options.add_argument(f"user-agent={ua}")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def extract_phone_ultimate(driver):
    """Ultimate phone extraction"""
    phone = "N/A"
    
    selectors = [
        "button[data-item-id*='phone']",
        "button[aria-label*='Phone']",
        "a[href^='tel:']",
        "[data-item-id*='phone'] span"
    ]
    
    for selector in selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            for attr in ['aria-label', 'href', 'title']:
                val = elem.get_attribute(attr)
                if val:
                    if 'tel:' in val:
                        val = val.replace('tel:', '')
                    clean = re.sub(r'\D', '', val)
                    if len(clean) >= 10:
                        return val
            
            text = elem.text.strip()
            if text and len(re.sub(r'\D', '', text)) >= 10:
                return text
        except:
            continue
    
    # Page source fallback
    try:
        source = driver.page_source
        patterns = [
            r'tel:([+\d\-\s\(\)]+)',
            r'\+91[\s-]?\d{10}',
            r'\d{10}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, source)
            for match in matches:
                clean = re.sub(r'\D', '', match)
                if 10 <= len(clean) <= 12:
                    return match.strip()
    except:
        pass
    
    return "N/A"

# MAIN SCRAPING
all_businesses = []
all_urls = set()  # Track unique URLs to avoid duplicates
total_phones = 0

try:
    for search_idx, query in enumerate(search_queries, 1):
        print(f"\n{'='*80}")
        print(f"🔍 SEARCH {search_idx}/{len(search_queries)}: {query}")
        print(f"{'='*80}")
        
        driver = create_stealth_driver()
        
        try:
            url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            
            print(f"🌐 Loading...")
            driver.get(url)
            time.sleep(random.uniform(5, 8))
            
            # Scroll
            print("📜 Scrolling...")
            scrollable = driver.find_element(By.CSS_SELECTOR, "div[role='feed']")
            
            for i in range(25):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
                time.sleep(random.uniform(1.5, 2.5))
            
            # Get URLs
            link_elements = driver.find_elements(By.CSS_SELECTOR, "a.hfpxzc")[:target_per_search]
            
            batch_links = []
            for elem in link_elements:
                try:
                    href = elem.get_attribute("href")
                    if href and "/maps/place/" in href and href not in all_urls:
                        batch_links.append(href)
                        all_urls.add(href)
                except:
                    continue
            
            print(f"✅ New URLs: {len(batch_links)} (Total unique: {len(all_urls)})")
            
            # Scrape batch
            for idx, biz_url in enumerate(batch_links, 1):
                global_idx = len(all_businesses) + 1
                print(f"#{global_idx}: ", end="", flush=True)
                
                try:
                    driver.get(biz_url)
                    time.sleep(random.uniform(3, 5))
                    
                    business_data = {
                        'rank': global_idx,
                        'url': biz_url,
                        'search_query': query,
                        'search_number': search_idx
                    }
                    
                    # Name
                    try:
                        name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf, h1").text
                        business_data['name'] = name[:100]
                        print(f"{name[:18]}...", end=" ")
                    except:
                        business_data['name'] = f"Business #{global_idx}"
                        print("[No name]", end=" ")
                    
                    # Address
                    try:
                        business_data['address'] = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']").text[:150]
                    except:
                        business_data['address'] = "N/A"
                    
                    # Phone
                    phone = extract_phone_ultimate(driver)
                    business_data['phone'] = phone
                    
                    if phone != "N/A":
                        total_phones += 1
                        print(f"✅📞", end=" ")
                    else:
                        print(f"❌📞", end=" ")
                    
                    # Website
                    try:
                        business_data['website'] = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']").get_attribute("href")
                    except:
                        business_data['website'] = "N/A"
                    
                    # Rating
                    try:
                        business_data['rating'] = driver.find_element(By.CSS_SELECTOR, "div.F7nice span[aria-hidden='true']").text
                    except:
                        business_data['rating'] = "N/A"
                    
                    # Reviews
                    try:
                        review_section = driver.find_element(By.CSS_SELECTOR, "div.F7nice")
                        match = re.search(r'\(([0-9,]+)\)', review_section.text)
                        business_data['reviews'] = match.group(1) if match else "0"
                    except:
                        business_data['reviews'] = "0"
                    
                    # Category
                    try:
                        cat = driver.find_element(By.CSS_SELECTOR, "button.DkEaL").text
                        business_data['category'] = cat.split("·")[0].strip()
                    except:
                        business_data['category'] = "N/A"
                    
                    all_businesses.append(business_data)
                    print(f"{business_data['rating']}⭐")
                    
                except Exception as e:
                    print(f"❌")
                    continue
            
            print(f"\n✅ Search {search_idx} done: {len(batch_links)} new businesses")
            print(f"📊 Running total: {len(all_businesses)} unique | 📞 Phones: {total_phones}")
            
        finally:
            driver.quit()
        
        # Save progress
        with open(f"gmb_progress_{len(all_businesses)}.json", "w", encoding="utf-8") as f:
            json.dump(all_businesses, f, indent=2, ensure_ascii=False)
        
        # Break between searches (except last)
        if search_idx < len(search_queries):
            delay = random.randint(3, 8)
            print(f"\n⏰ Cooling {delay} minutes before next search...")
            time.sleep(delay * 60)
    
    # FINAL SAVE
    print(f"\n{'='*80}")
    print("🎉 MULTI-SEARCH COMPLETE!")
    print(f"{'='*80}")
    print(f"✅ Total unique businesses: {len(all_businesses)}")
    print(f"📞 Phones found: {total_phones} ({total_phones/len(all_businesses)*100:.1f}%)")
    print(f"🔍 Searches performed: {len(search_queries)}")
    
    # Save final
    json_file = f"gmb_MULTI_{len(all_businesses)}_{main_city}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_businesses, f, indent=2, ensure_ascii=False)
    
    csv_file = f"gmb_MULTI_{len(all_businesses)}_{main_city}.csv"
    if all_businesses:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_businesses[0].keys())
            writer.writeheader()
            writer.writerows(all_businesses)
    
    print(f"\n💾 Files saved:")
    print(f"   {json_file}")
    print(f"   {csv_file}")
    
    # Stats by area
    print(f"\n📊 Results by search area:")
    from collections import Counter
    search_counts = Counter([b['search_query'] for b in all_businesses])
    for query, count in search_counts.most_common(10):
        print(f"   {query[:40]}: {count} businesses")

except KeyboardInterrupt:
    print("\n\n⚠️ Stopped!")
    if all_businesses:
        with open(f"gmb_interrupted_{len(all_businesses)}.json", "w") as f:
            json.dump(all_businesses, f, indent=2)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
