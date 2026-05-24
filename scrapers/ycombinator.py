import requests

def scrape():
    results = []
    seen = set()
    for batch in ["W25","S24","W24","S25"]:
        try:
            resp = requests.get("https://api.ycombinator.com/v0.1/companies", params={"batch": batch}, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            for c in resp.json().get("companies", [])[:15]:
                name = c.get("name","").strip()
                if not name or name in seen:
                    continue
                seen.add(name)
                results.append({"name": name, "tagline": c.get("one_liner","")[:200], "url": c.get("website",""), "batch": c.get("batch", batch), "source": "yc"})
        except Exception as e:
            print(f"[YC] batch {batch} failed: {e}")
    print(f"[YCombinator] Scraped {len(results)} companies")
    return results
