import aiohttp
import time
from bs4 import BeautifulSoup

async def analyze_website(url: str):
    if not url:
        return {"ssl_enabled": False, "mobile_friendly": False, "load_time": 0.0}
        
    ssl_enabled = url.startswith("https")
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                html = await response.text()
                load_time = time.time() - start_time
                
                soup = BeautifulSoup(html, 'html.parser')
                # Check for mobile viewport meta tag
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                mobile_friendly = viewport is not None
                
                return {
                    "ssl_enabled": ssl_enabled,
                    "mobile_friendly": mobile_friendly,
                    "load_time": round(load_time, 2)
                }
    except Exception:
        return {"ssl_enabled": ssl_enabled, "mobile_friendly": False, "load_time": 99.9}

def calculate_lead_score(has_website, rating, reviews, has_phone):
    score = 0
    if not has_website: score += 4
    if rating and rating > 4.0: score += 2
    if reviews and reviews > 20: score += 1
    if has_phone: score += 1
    return score

def determine_lead_type(has_website, mobile_friendly):
    if not has_website:
        return "NO_WEBSITE"
    if not mobile_friendly:
        return "WEBSITE_REDESIGN"
    return "NORMAL"
