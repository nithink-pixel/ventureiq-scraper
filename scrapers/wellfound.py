import requests
from bs4 import BeautifulSoup

def scrape():
    results = []
    try:
        resp = requests.get("https://wellfound.com/startups", timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "lxml")
        seen = set()
        for link in soup.select("a[href*='/company/']")[:30]:
            name = link.get_text(strip=True)
            href = link.get("href","")
            if not name or name in seen or len(name) < 2:
                continue
            seen.add(name)
            results.append({"name": name, "tagline": "", "url": f"https://wellfound.com{href}" if href.startswith("/") else href, "open_roles": 0, "source": "wellfound"})
    except Exception as e:
        print(f"[Wellfound] failed: {e}")
    print(f"[Wellfound] Scraped {len(results)} companies")
    return results
