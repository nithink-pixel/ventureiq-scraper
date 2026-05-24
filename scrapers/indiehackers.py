import requests
from bs4 import BeautifulSoup

def scrape():
    results = []
    try:
        resp = requests.get("https://www.indiehackers.com/products", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "lxml")
        seen = set()
        for card in soup.select("a[href*='/product/']")[:30]:
            name_el = card.find(["h2","h3","strong"])
            name = name_el.get_text(strip=True) if name_el else card.get_text(strip=True)[:50]
            href = card.get("href","")
            if not name or name in seen or len(name) < 2:
                continue
            seen.add(name)
            results.append({"name": name, "tagline": "", "url": f"https://www.indiehackers.com{href}" if href.startswith("/") else href, "source": "indiehackers"})
    except Exception as e:
        print(f"[IndieHackers] failed: {e}")
    print(f"[IndieHackers] Scraped {len(results)} products")
    return results
