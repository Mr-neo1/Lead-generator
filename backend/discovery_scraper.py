import asyncio
from playwright.async_api import async_playwright
import random
import logging
import re
import os
import hashlib

logger = logging.getLogger(__name__)

# Configurable delays from environment
SCRAPE_DELAY_MIN = float(os.getenv("SCRAPE_DELAY_MIN", "1.0"))
SCRAPE_DELAY_MAX = float(os.getenv("SCRAPE_DELAY_MAX", "3.0"))

# Expanded user agents rotation (20+ agents for better anti-detection)
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Firefox Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Firefox Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
    # Safari Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Edge Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    # Chrome Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Firefox Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
]

async def scrape_google_maps_grid(keyword: str, lat: float, lng: float, max_results: int = 120):
    """
    Scrape Google Maps search results for a specific keyword at given coordinates.
    
    Args:
        keyword: Search term (e.g., "dentist", "gym")
        lat: Latitude coordinate
        lng: Longitude coordinate
        max_results: Maximum number of results to collect (Google typically limits to ~120)
    
    Returns:
        List of business dictionaries with place_id, name, maps_url, lat, lng
    """
    results = []
    
    async with async_playwright() as p:
        # Launch browser with anti-detection args
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )
        
        # Randomize viewport for fingerprint variation
        viewport_options = [
            {'width': 1920, 'height': 1080},
            {'width': 1536, 'height': 864},
            {'width': 1440, 'height': 900},
            {'width': 1366, 'height': 768},
            {'width': 1280, 'height': 720},
        ]
        
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport=random.choice(viewport_options),
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': lat, 'longitude': lng},
            permissions=['geolocation']
        )
        
        page = await context.new_page()
        
        # Anti-detection scripts
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
        """)
        
        try:
            # Search URL with coordinates
            url = f"https://www.google.com/maps/search/{keyword}/@{lat},{lng},15z"
            logger.info(f"Navigating to: {url}")
            
            # Random delay before navigation
            await asyncio.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))
            
            await page.goto(url, timeout=45000, wait_until='domcontentloaded')
            await asyncio.sleep(random.uniform(3, 6))  # Anti-blocking delay
            
            # Wait for results panel with fallback selectors
            feed_selectors = [
                'div[role="feed"]',
                'div[role="list"]',
                'div.m6QErb',  # Google Maps results container
                '[data-value="Search results"]'
            ]
            
            feed = None
            for selector in feed_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=8000)
                    feed = await page.query_selector(selector)
                    if feed:
                        logger.info(f"Found results container with selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not feed:
                logger.warning("Results feed not found with any selector, trying to proceed anyway")
                await asyncio.sleep(3)
            
            # Scroll to load more results
            scroll_count = 0
            max_scrolls = 12
            prev_count = 0
            no_new_results_count = 0
            
            while scroll_count < max_scrolls and len(results) < max_results:
                # Find the scrollable container with fallback
                for selector in feed_selectors:
                    feed = await page.query_selector(selector)
                    if feed:
                        break
                
                if feed:
                    # Scroll with human-like behavior
                    scroll_amount = random.randint(300, 600)
                    await page.evaluate(f'''
                        (element) => {{
                            element.scrollBy({{ top: {scroll_amount}, behavior: 'smooth' }});
                        }}
                    ''', feed)
                
                # Random delay between scrolls
                await asyncio.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX * 1.5))
                
                # Extract business links with multiple selectors
                link_selectors = [
                    'a[href*="/maps/place/"]',
                    'a.hfpxzc',  # Direct place link class
                    'div[role="article"] a[href*="place"]'
                ]
                
                elements = []
                for selector in link_selectors:
                    try:
                        found = await page.query_selector_all(selector)
                        if found:
                            elements = found
                            break
                    except Exception:
                        continue
                
                for el in elements:
                    try:
                        href = await el.get_attribute('href')
                        name = await el.get_attribute('aria-label')
                        
                        if href and name:
                            place_id = extract_place_id(href)
                            
                            # Validate place_id
                            if place_id and len(place_id) > 3 and not any(r['place_id'] == place_id for r in results):
                                results.append({
                                    "place_id": place_id,
                                    "name": clean_business_name(name),
                                    "maps_url": href if href.startswith('http') else f"https://www.google.com{href}",
                                    "lat": lat,
                                    "lng": lng
                                })
                    except Exception as e:
                        logger.debug(f"Error extracting element: {e}")
                        continue
                
                # Check progress
                if len(results) == prev_count:
                    no_new_results_count += 1
                    if no_new_results_count >= 3:
                        scroll_count += 1
                        no_new_results_count = 0
                else:
                    no_new_results_count = 0
                    scroll_count = 0
                
                prev_count = len(results)
                logger.info(f"Scroll {scroll_count}/{max_scrolls}: found {len(results)} businesses")
                
                # Check for "end of results" indicators
                end_indicators = [
                    'text="You\'ve reached the end of the list"',
                    'text="No more results"',
                    'div.HlvSq'  # End of list div
                ]
                
                for indicator in end_indicators:
                    try:
                        end_elem = await page.query_selector(indicator)
                        if end_elem:
                            logger.info("Reached end of results")
                            scroll_count = max_scrolls
                            break
                    except Exception:
                        continue
            
            logger.info(f"Completed scraping: {len(results)} businesses found")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            await browser.close()
    
    return results


def clean_business_name(name: str) -> str:
    """Clean and normalize business name."""
    if not name:
        return ""
    # Remove common suffixes that might be in the name
    name = re.sub(r'\s*\·\s*.*$', '', name)  # Remove everything after ·
    name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
    return name[:200]  # Limit length

def extract_place_id(url: str) -> str:
    """Extract a unique identifier from the Google Maps URL"""
    try:
        # Try to extract the place name from URL as a fallback ID
        # Format: /maps/place/Business+Name/@...
        match = re.search(r'/maps/place/([^/@]+)', url)
        if match:
            return match.group(1)
        
        # Extract from data parameter if available
        if '/data=' in url:
            data_part = url.split('/data=')[0]
            parts = data_part.split('/')
            if len(parts) >= 2:
                return parts[-2] if parts[-1].startswith('@') else parts[-1]
        
        # Fallback: use deterministic hash of URL (consistent across restarts)
        return hashlib.md5(url.encode()).hexdigest()[:16]
    except Exception:
        return hashlib.md5(url.encode()).hexdigest()[:16]
