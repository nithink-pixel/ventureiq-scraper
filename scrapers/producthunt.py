import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
load_dotenv()

PH_API_KEY = os.getenv("PH_API_KEY", "")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

GRAPHQL_QUERY = """
query { posts(first: 30, order: VOTES) { edges { node {
  name tagline url votesCount
  topics { edges { node { name } } }
} } } }
"""

def scrape():
    if PH_API_KEY:
        print("[ProductHunt] Using official API...")
        try:
            resp = requests.post(
                "https://api.producthunt.com/v2/api/graphql",
                json={"query": GRAPHQL_QUERY},
                headers={**HEADERS, "Authorization": f"Bearer {PH_API_KEY}", "Content-Type": "application/json"},
                timeout=20,
            )
            edges = resp.json().get("data", {}).get("posts", {}).get("edges", [])
            results = []
            for edge in edges:
                n = edge.get("node", {})
                if not n.get("name"): continue
                results.append({"name": n["name"].strip(), "tagline": n.get("tagline","")[:200], "url": n.get("url",""), "upvotes": n.get("votesCount",0), "source": "producthunt"})
            print(f"[ProductHunt] API returned {len(results)} products")
            return results
        except Exception as e:
            print(f"[ProductHunt] API failed: {e}, trying scrape...")

    results = []
    for url in ["https://www.producthunt.com/", "https://www.producthunt.com/posts"]:
        try:
            print(f"[ProductHunt] Scraping {url}...")
            resp = requests.get(url, headers=HEADERS, timeout=20)
            soup = BeautifulSoup(resp.text, "lxml")
            seen = set()
            links = soup.find_all("a", href=lambda h: h and "/posts/" in h)
            for link in links[:40]:
                href = link.get("href","")
                if href in seen: continue
                seen.add(href)
                heading = link.find(["h2","h3","h1"])
                name = heading.get_text(strip=True) if heading else link.get_text(strip=True)[:60]
                if not name or len(name) < 3: continue
                p = link.find("p")
                tagline = p.get_text(strip=True)[:200] if p else ""
                full_url = f"https://www.producthunt.com{href}" if href.startswith("/") else href
                results.append({"name": name, "tagline": tagline, "url": full_url, "upvotes": 0, "source": "producthunt"})
            if results:
                break
        except Exception as e:
            print(f"[ProductHunt] Error: {e}")
    print(f"[ProductHunt] Scraped {len(results)} products")
    return results

if __name__ == "__main__":
    for d in scrape()[:5]: print(d)
