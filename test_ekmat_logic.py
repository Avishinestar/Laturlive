import requests
from bs4 import BeautifulSoup
import re
import datetime
import json

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def data_serializer(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def test_ekmat():
    latur_link = "https://epaper.dainikekmat.com/edition/21568/latur" # Hardcoded for test matching aggregator
    news_items = []
    
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
        else:
            print("ERROR: #print_img not found!")
        
        # 2. Find Reference Map Width
        map_img = p3_soup.find(id='mapimage')
        ref_width = 945 # Default fallback
        if map_img:
            src = map_img.get('src', '')
            match = re.search(r'width=(\d+)', src)
            if match:
                ref_width = int(match.group(1))
        else:
            print("WARNING: #mapimage not found, using default 945")

        # 3. Process Areas
        areas = p3_soup.find_all('area')
        print(f"Found {len(areas)} areas.")
        
        clip_count = 0
        global_ratio = None
        
        for area in areas:
            if clip_count >= 15: break 
            
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
                        print(f"Calculated Global Ratio: {global_ratio} (DataW {data_w} / CoordW {coord_w})")
                
                # Calculate estimated High Res Full Width
                full_width_est = ref_width * (global_ratio if global_ratio else 1)

                if high_res_url:
                   item = {
                        "source": "Dainik Ekmat",
                        "title": f"Ekmat News Clip",
                        "link": page3_link, 
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
                    }
                   news_items.append(item)
                   clip_count += 1
                   
            except Exception as area_err:
                print(f"Area Error: {area_err}")
                continue 

    except Exception as e:
        print(f"Failed to scrape Ekmat clips: {e}")

    print(f"\nTotal Items Generated: {len(news_items)}")
    # Dump one item to see structure
    if news_items:
        print(json.dumps(news_items[0], default=data_serializer, indent=2))

test_ekmat()
