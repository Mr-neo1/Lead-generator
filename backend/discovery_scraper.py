import asyncio
from playwright.async_api import async_playwright
import random
import logging
import re

logger = logging.getLogger(__name__)

# User agents rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
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
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        page = await context.new_page()
        
        try:
            # Search URL with coordinates
            url = f"https://www.google.com/maps/search/{keyword}/@{lat},{lng},15z"
            logger.info(f"Navigating to: {url}")
            
            await page.goto(url, timeout=30000)
            await asyncio.sleep(random.uniform(3, 5))  # Anti-blocking delay
            
            # Wait for results panel to load
            try:
                await page.wait_for_selector('div[role="feed"]', timeout=10000)
            except:
                logger.warning("Results feed not found, trying alternative selector")
                await asyncio.sleep(2)
            
            # Scroll to load more results
            scroll_count = 0
            max_scrolls = 10
            prev_count = 0
            
            while scroll_count < max_scrolls and len(results) < max_results:
                # Find the scrollable container
                feed = await page.query_selector('div[role="feed"]')
                if feed:
                    # Scroll down
                    await page.evaluate('''
                        (element) => {
                            element.scrollTop = element.scrollHeight;
                        }
                    ''', feed)
                
                await asyncio.sleep(random.uniform(1.5, 3))  # Wait for content to load
                
                # Extract business links
                elements = await page.query_selector_all('a[href*="/maps/place/"]')
                
                for el in elements:
                    try:
                        href = await el.get_attribute('href')
                        name = await el.get_attribute('aria-label')
                        
                        if href and name:
                            # Extract place_id from URL
                            # Format: /maps/place/Name/@lat,lng,zoom/data=...
                            place_id = extract_place_id(href)
                            
                            # Check for duplicates
                            if place_id and not any(r['place_id'] == place_id for r in results):
                                results.append({
                                    "place_id": place_id,
                                    "name": name,
                                    "maps_url": href if href.startswith('http') else f"https://www.google.com{href}",
                                    "lat": lat,
                                    "lng": lng
                                })
                    except Exception as e:
                        logger.debug(f"Error extracting element: {e}")
                        continue
                
                # Check if we got new results
                if len(results) == prev_count:
                    scroll_count += 1  # No new results, increment scroll count
                else:
                    scroll_count = 0  # Reset if we found new results
                    prev_count = len(results)
                
                logger.info(f"Scroll iteration: found {len(results)} businesses so far")
                
                # Check for "end of results" indicator
                end_text = await page.query_selector('text="You\'ve reached the end of the list"')
                if end_text:
                    logger.info("Reached end of results")
                    break
            
            logger.info(f"Completed scraping: {len(results)} businesses found")
            
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        finally:
            await browser.close()
    
    return results

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
        
        # Fallback: use hash of URL
        return str(hash(url))
    except:
        return str(hash(url))
