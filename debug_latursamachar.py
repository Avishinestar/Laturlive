import requests
from bs4 import BeautifulSoup
import re

url = "https://www.latursamachar.com/view/933/latur-main"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.content, 'html.parser')

    print("\n--- Dumping Script Content ---")
    with open("latursamachar_scripts.txt", "w", encoding="utf-8") as f:
        scripts = soup.find_all('script')
        for i, s in enumerate(scripts):
            if s.string:
                f.write(f"\n--- Script {i} ---\n")
                f.write(s.string)
    print("Scripts dumped to latursamachar_scripts.txt")

except Exception as e:
    print(f"Error: {e}")
