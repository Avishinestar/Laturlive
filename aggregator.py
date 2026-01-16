import requests
from bs4 import BeautifulSoup
import json
import time
import schedule
import datetime
import dateparser
import os
import re

# Application Constants
DATA_FILE = "news_data.json"
DATA_JS_FILE = "news_data.js"
MAX_ITEMS_PER_SOURCE = 15
LATUR_KEYWORDS = ["Latur", "लातूर", "latur"]

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,mr;q=0.8"
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'\s+', ' ', text).strip()

def is_within_last_3_days(date_obj):
    if not date_obj: return True # Default to true if date parsing fails to avoid empty feed
    cutoff = datetime.datetime.now() - datetime.timedelta(days=3)
    return date_obj > cutoff

def parse_relative_date(date_str):
    if not date_str: return None
    return dateparser.parse(date_str)

def fetch_abp_latur():
    print("Fetching ABP Live Latur...")
    url = "https://marathi.abplive.com/news/latur"
    news_items = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Robust Strategy: distinct article links usually have /news/latur/ in them
        # We collect all such unique links
        seen_links = set()
        
        links = soup.find_all('a', href=True)
        for a in links:
            if len(news_items) >= MAX_ITEMS_PER_SOURCE: break
            
            href = a['href']
            # ABP Link pattern: /news/latur/...
            if '/news/latur/' in href and href not in seen_links:
                seen_links.add(href)
                
                title = clean_text(a.get_text())
                # If title is too short, it might be a 'Read More' button or image link. Try to find title in parent or image alt
                if len(title) < 10:
                    img = a.find('img')
                    if img and img.get('alt'): title = clean_text(img.get('alt'))
                    
                if len(title) < 15: continue # Skip if still no good title
                
                if not href.startswith('http'): href = "https://marathi.abplive.com" + href
                
                # Try to find image
                image = None
                img_tag = a.find('img')
                if img_tag:
                     image = img_tag.get('data-src') or img_tag.get('src')
                
                # If no image in A tag, look in parent div
                if not image:
                    parent = a.find_parent('div')
                    if parent:
                        p_img = parent.find('img')
                        if p_img: image = p_img.get('data-src') or p_img.get('src')
                
                news_items.append({
                    "source": "ABP Majha",
                    "title": title,
                    "link": href,
                    "image": image, # May be None
                    "time_str": "Recent",
                    "timestamp": datetime.datetime.now().isoformat()
                })

    except Exception as e:
        print(f"Failed to fetch ABP: {e}")
    return news_items

def fetch_lokmat_latur():
    print("Fetching Lokmat Latur...")
    url = "https://www.lokmat.com/latur/"
    news_items = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Robust Strategy: Find all links pointing to latur news articles
        seen_links = set()
        links = soup.find_all('a', href=True)
        
        for a in links:
            if len(news_items) >= MAX_ITEMS_PER_SOURCE: break
            
            href = a['href']
            # Lokmat article links usually look like /latur/<slug>/
            # We filter out the main page itself and other non-article pages if possible
            if '/latur/' in href and href.strip('/') != '/latur' and href not in seen_links:
                 
                 # Additional check: exclude 'page' pagination links if distinct
                 if 'page/' in href: continue

                 seen_links.add(href)
                 
                 title = clean_text(a.get_text())
                 # If text is empty, check nested elements or title attribute
                 if len(title) < 15:
                     t_attr = a.get('title')
                     if t_attr: title = clean_text(t_attr)
                     
                 # Fallback: Look for h2/h3 inside
                 if len(title) < 15:
                     h = a.find(['h2', 'h3', 'h4'])
                     if h: title = clean_text(h.get_text())
                 
                 if len(title) < 15: continue
                 
                 if not href.startswith('http'): href = "https://www.lokmat.com" + href
                 
                 # Try to find image
                 image = None
                 # Check for img inside anchor
                 img = a.find('img')
                 if img: image = img.get('data-src') or img.get('src')
                 
                 # If not, check parent figure/div for image
                 if not image:
                     parent = a.find_parent(['figure', 'div', 'article'])
                     if parent:
                         p_img = parent.find('img')
                         if p_img: image = p_img.get('data-src') or p_img.get('src')

                 news_items.append({
                    "source": "Lokmat",
                    "title": title,
                    "link": href,
                    "image": image,
                    "time_str": "Recent", 
                    "timestamp": datetime.datetime.now().isoformat()
                 })

    except Exception as e:
        print(f"Failed to fetch Lokmat: {e}")
    return news_items

        
def fetch_pudhari_latur():
    print("Fetching Pudhari Latur...")
    url = "https://pudhari.news/maharashtra/marathwada/latur"
    news_items = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        seen_links = set()
        links = soup.find_all('a', href=True)
        
        for a in links:
             if len(news_items) >= MAX_ITEMS_PER_SOURCE: break
             href = a['href']
             
             # Pudhari link pattern usually includes the category path or just checks for uniqueness
             if '/latur/' in href and href not in seen_links:
                seen_links.add(href)
                
                title = clean_text(a.get_text())
                if len(title) < 15: 
                    # Try finding h1-h6 inside
                    h = a.find(['h1','h2','h3','h4','h5','h6'])
                    if h: title = clean_text(h.get_text())
                    
                if len(title) < 15: continue
                
                if not href.startswith('http'): href = "https://pudhari.news" + href

                # Image attempt
                image = None
                img = a.find('img')
                if img: image = img.get('src')
                # Try parent container for image if likely
                if not image:
                    parent = a.find_parent('div')
                    if parent:
                         img = parent.find('img')
                         if img: image = img.get('src')

                news_items.append({
                    "source": "Pudhari",
                    "title": title,
                    "link": href,
                    "image": image,
                    "time_str": "Recent",
                    "timestamp": datetime.datetime.now().isoformat()
                })

    except Exception as e:
        print(f"Failed to fetch Pudhari: {e}")
    return news_items


def fetch_mclatur():
    print("Fetching MC Latur...")
    url = "https://mclatur.org/"
    news_items = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Typically looking for a ticker or "Latest Updates" section
        # We'll extract links from the marquee or a specific 'news' section
        links = soup.find_all('a', href=True)
        
        count = 0
        for a in links:
            if count >= 10: break
            link = a['href']
            text = clean_text(a.get_text())
            
            # Simple heuristic: link text longer than 20 chars is likely a headline
            if len(text) > 20 and ("tender" not in text.lower()): 
                if not link.startswith('http'): link = "https://mclatur.org/" + link.lstrip('/')
                
                news_items.append({
                    "source": "MCLatur (Govt)",
                    "title": text,
                    "link": link,
                    "image": "https://mclatur.org/images/logo.png", # Placeholder/Logo
                    "time_str": "Official Update",
                    "timestamp": datetime.datetime.now().isoformat()
                })
                count += 1
    except Exception as e:
        print(f"Failed to fetch MCLatur: {e}")
    return news_items

def fetch_punyanagari():
    print("Fetching Punyanagari E-Paper...")
    news_items = []
    try:
        # Construct dynamic URL for today
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        link = f"https://epaper.punyanagari.in/edition/Latur/PNAGARI_LTR/date/{today_str}/page/1"
        
        # Verify if it exists (Optional, but good practice. E-papers might use different date formats or be late)
        # For now, we trust the pattern.
        
        news_items.append({
            "source": "Punyanagari E-Paper",
            "title": f"Punyanagari E-Paper ({today_str})",
            "link": link,
            "image": "https://epaper.punyanagari.in/assets/images/logo.png", # Placeholder or logo
            "time_str": "Today's Edition",
            "timestamp": datetime.datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Failed to fetch Punyanagari: {e}")
    return news_items

def fetch_latursamachar():
    print("Fetching Latur Samachar...")
    news_items = []
    try:
        # Follow redirect to get latest edition
        base_url = "https://www.latursamachar.com/epaper/default/open?id=9"
        response = requests.get(base_url, headers=HEADERS, allow_redirects=True, timeout=10)
        final_url = response.url
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract EpaperData JSON from script
        # Pattern: const EpaperData = {...};
        scripts = soup.find_all('script')
        epaper_data = None
        
        for s in scripts:
            if s.string and 'const EpaperData =' in s.string:
                match = re.search(r'const EpaperData\s*=\s*({.*?});', s.string, re.DOTALL)
                if match:
                    try:
                        epaper_data = json.loads(match.group(1))
                        break
                    except:
                        pass # JSON parsing might fail if regex was imperfect
        
        if epaper_data and 'pgModels' in epaper_data:
            # We found the data!
            today_str = datetime.date.today().strftime("%d-%m-%Y")
            
            # Sort pages by order logic if needed, usually keys are "1", "2"...
            for key, page in epaper_data['pgModels'].items():
                title = f"Latur Samachar - {page.get('pg_title', 'Page ' + key)}"
                
                # Construct Page URL: base/page_order
                # final_url typically ends with /view/ID/alias
                # Page link: .../view/ID/alias/ORDER
                page_link = f"{final_url}/{page.get('pg_order', key)}"
                
                # Construct Image URL
                # Path: /media/FOLDER/FILENAME
                img_path = page['attachment'].get('f_folder', '') + "/" + page['attachment'].get('f_filename', '')
                image = f"https://www.latursamachar.com/media/{img_path}"
                
                news_items.append({
                    "source": "Latur Samachar",
                    "title": f"{title} ({today_str})",
                    "link": page_link,
                    "image": image,
                    "time_str": "Today's Edition",
                    "timestamp": datetime.datetime.now().isoformat()
                })
        else:
             # Fallback if parsing fails
             print("Could not parse EpaperData, using fallback.")
             today_str = datetime.date.today().strftime("%d-%m-%Y")
             news_items.append({
                "source": "Latur Samachar",
                "title": f"Latur Samachar E-Paper ({today_str})",
                "link": final_url,
                "image": "https://www.latursamachar.com/assets/images/logo.png",
                "time_str": "Today's Edition",
                "timestamp": datetime.datetime.now().isoformat()
            })

    except Exception as e:
        print(f"Failed to fetch Latur Samachar: {e}")
    return news_items

def fetch_ekmat():
    print("Fetching Dainik Ekmat...")
    news_items = []
    try:
        url = "https://epaper.dainikekmat.com/"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all latur links
        latur_links = []
        for a in soup.find_all('a', href=True):
            href = str(a.get('href')).strip()
            text = a.get_text().lower()
            if (('latur' in text or 'latur' in href.lower()) and 
                len(href) > 2 and 'javascript' not in href and href != '#'):
                latur_links.append(href)
        
        if latur_links:
            # Prioritize links with "edition" in them
            edition_links = [l for l in latur_links if 'edition' in l]
            if edition_links:
                latur_link = edition_links[0]
            else:
                latur_link = latur_links[0]

            if not latur_link.startswith('http'): latur_link = url.rstrip('/') + "/" + latur_link.lstrip('/')

            print(f"Found Ekmat Link: {latur_link}")
            news_items.append({
                "source": "Dainik Ekmat",
                "title": f"Dainik Ekmat E-Paper (Main Edition)",
                "link": latur_link,
                "image": "https://epaper.dainikekmat.com/assets/images/logo.png",
                "time_str": "Today's Edition",
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # --- EKMAT PAGE 3 CLIP SCRAPER ---
            try:
                page3_link = f"{latur_link}/page/3"
                print(f"Fetching Ekmat Page 3 Clips from: {page3_link}")
                p3_resp = requests.get(page3_link, headers=HEADERS, timeout=15)
                p3_soup = BeautifulSoup(p3_resp.content, 'html.parser')
                
                # 1. Find High Res Image
                print_img = p3_soup.find(id='print_img')
                high_res_url = None
                if print_img:
                    high_res_url = print_img.get('src')
                
                # 2. Find Reference Map Width
                # Usually in #mapimage src "...&width=945"
                map_img = p3_soup.find(id='mapimage')
                ref_width = 945 # Default fallback
                if map_img:
                    src = map_img.get('src', '')
                    match = re.search(r'width=(\d+)', src)
                    if match:
                        ref_width = int(match.group(1))

                # 3. Process Areas
                areas = p3_soup.find_all('area')
                clip_count = 0
                
                # Calculate global scale ratio using the first valid area
                # Ratio = data-w / (coords_x2 - coords_x1)
                global_ratio = None
                
                for area in areas:
                    if clip_count >= 15: break # Limit clips
                    
                    try:
                        coords = [float(x) for x in area.get('coords').split(',')]
                        data_x = float(area.get('data-x'))
                        data_y = float(area.get('data-y'))
                        data_w = float(area.get('data-w'))
                        data_h = float(area.get('data-h'))
                        
                        # Calculate ratio if not yet known
                        if global_ratio is None:
                            coord_w = coords[2] - coords[0]
                            if coord_w > 0:
                                global_ratio = data_w / coord_w
                        
                        # Calculate estimated High Res Full Width
                        # FullWidth = RefWidth * Ratio
                        full_width_est = ref_width * (global_ratio if global_ratio else 1)

                        if high_res_url:
                           news_items.append({
                                "source": "Dainik Ekmat",
                                "title": f"Ekmat News Clip",
                                "link": page3_link, # Link to page for fallback
                                "image": high_res_url,
                                "clip": {
                                    "x": data_x,
                                    "y": data_y,
                                    "w": data_w,
                                    "h": data_h,
                                    "full_width": full_width_est
                                },
                                "time_str": "Short News",
                                "timestamp": datetime.datetime.now().isoformat()
                            })
                           clip_count += 1
                           
                    except Exception as area_err:
                        continue # Skip bad area

            except Exception as e:
                print(f"Failed to scrape Ekmat clips: {e}")
                with open("error.txt", "w") as f:
                    f.write(f"Ekmat Error: {str(e)}")
                # Fallback to simple Page 3 link if scraping failed
                news_items.append({
                    "source": "Dainik Ekmat",
                    "title": f"Dainik Ekmat - Latur Local (Page 3)",
                    "link": f"{latur_link}/page/3",
                    "image": "https://epaper.dainikekmat.com/assets/images/logo.png",
                    "time_str": "Local News",
                    "timestamp": datetime.datetime.now().isoformat()
                })

        else:
            print("No Ekmat Latur links found on homepage.")

    except Exception as e:
        print(f"Failed to fetch Ekmat: {e}")
    return news_items

def fetch_divya_marathi():
    print("Fetching Divya Marathi...")
    news_items = []
    try:
        # Fetch Maharashtra Local page
        base_url = "https://divyamarathi.bhaskar.com"
        url = "https://divyamarathi.bhaskar.com/local/maharashtra/"
        print(f"Scanning {url} for Latur news...")
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for headlines in h3, h2, or li text
        # print("Page Title:", soup.title.string) 
        
        articles = soup.find_all('li')
        count = 0
        seen_titles = set()

        for art in articles:
            if count >= MAX_ITEMS_PER_SOURCE: break
            
            text_content = art.get_text()
            # print(f"Checking article: {text_content[:50]}...")
            
            # Filter for Latur related content - Check both English and Marathi spellings
            if "latur" in text_content.lower() or "लातूर" in text_content:
                a_tag = art.find('a')
                if not a_tag: continue
                
                link = a_tag.get('href')
                if not link: continue
                if not link.startswith('http'): link = base_url + link
                
                title = a_tag.get('title')
                if not title:
                     t_tag = art.find(['h3', 'h2', 'h4', 'p'])
                     if t_tag: title = t_tag.get_text().strip()
                     else: title = clean_text(text_content)[:100] + "..."
                
                if title in seen_titles: continue
                seen_titles.add(title)

                img_tag = art.find('img')
                image = img_tag.get('src') if img_tag else None
                if img_tag and img_tag.get('data-src'): image = img_tag.get('data-src')

                print(f"Found Divya Marathi Article: {title}")
                news_items.append({
                    "source": "Divya Marathi",
                    "title": title,
                    "link": link,
                    "image": image,
                    "time_str": "Recent",
                    "timestamp": datetime.datetime.now().isoformat()
                })
                count += 1
                
        if count == 0:
             print("No specific Latur news found on Divya Marathi Maharashtra page.")

    except Exception as e:
        print(f"Failed to fetch Divya Marathi: {e}")
    return news_items

def aggregate_news():
    print(f"\n--- Starting Aggregation at {datetime.datetime.now()} ---")
    all_news = []
    
    all_news.extend(fetch_abp_latur())
    all_news.extend(fetch_lokmat_latur())
    all_news.extend(fetch_pudhari_latur())
    all_news.extend(fetch_mclatur())
    all_news.extend(fetch_punyanagari())
    all_news.extend(fetch_latursamachar())
    all_news.extend(fetch_ekmat())
    all_news.extend(fetch_divya_marathi())
    
    # Filter by date (last 3 days) - strictly speaking we already fetched recent, but let's double check timestamps if valid
    # Also deduplicate by Title
    unique_news = {}
    for item in all_news:
        if item['title'] not in unique_news:
            # Check date if possible
            if is_within_last_3_days(dateparser.parse(item['timestamp'])):
                unique_news[item['title']] = item
    
    final_list = list(unique_news.values())
    
    # Sort by 'timestamp' descending usually, but mixed sources make this hard. 
    # We'll just keep them in order of fetch or randomize, but usually latest first.
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    # Also save as a JS file for local file:// access without CORS issues
    with open(DATA_JS_FILE, 'w', encoding='utf-8') as f:
        json_str = json.dumps(final_list, ensure_ascii=False, indent=2)
        f.write(f"window.newsData = {json_str};")

    print(f"Updated {DATA_FILE} and {DATA_JS_FILE} with {len(final_list)} articles.")

def main():
    # Run once immediately and EXIT.
    # We do not use the while loop here because GitHub Actions triggers the script every 30 mins.
    try:
        aggregate_news()
    except Exception as e:
        print(f"Error in main execution: {e}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
