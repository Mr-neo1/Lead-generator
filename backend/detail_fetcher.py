from playwright.async_api import async_playwright
import asyncio
import random
import re
import logging
from urllib.parse import unquote

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

async def fetch_place_details(maps_url: str) -> dict:
    """
    Fetch business details from a Google Maps place URL using Playwright.
    
    Uses headless browser to render JavaScript and extract actual business details.
    
    Returns:
        Dictionary with website, phone, rating, reviews, category, address
    """
    result = {
        "website": None,
        "phone": None,
        "rating": None,
        "reviews": None,
        "category": None,
        "address": None
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": 1080},
                locale="en-US"
            )
            page = await context.new_page()
            
            # Anti-detection
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            
            # Random delay before request
            await asyncio.sleep(random.uniform(1, 3))
            
            try:
                await page.goto(maps_url, wait_until="networkidle", timeout=30000)
                await asyncio.sleep(random.uniform(2, 4))  # Wait for JS to render
                
                # Try to extract phone number
                phone_selectors = [
                    'button[data-item-id^="phone:"]',
                    'a[data-item-id^="phone:"]',
                    '[data-tooltip="Copy phone number"]',
                    'button[aria-label*="Phone"]',
                    '[data-item-id*="phone"]'
                ]
                
                for selector in phone_selectors:
                    try:
                        phone_elem = await page.query_selector(selector)
                        if phone_elem:
                            phone_text = await phone_elem.inner_text()
                            if phone_text:
                                # Clean up phone number
                                phone_clean = re.sub(r'[^\d+\-\(\)\s]', '', phone_text).strip()
                                if len(re.sub(r'\D', '', phone_clean)) >= 10:
                                    result["phone"] = phone_clean
                                    break
                    except:
                        continue
                
                # Try backup: look for phone in aria-labels
                if not result["phone"]:
                    try:
                        buttons = await page.query_selector_all('button[aria-label]')
                        for btn in buttons:
                            label = await btn.get_attribute('aria-label')
                            if label and 'phone' in label.lower():
                                # Extract phone from aria-label like "Phone: +91 98765 43210"
                                phone_match = re.search(r'[\d\s\+\-\(\)]{10,}', label)
                                if phone_match:
                                    result["phone"] = phone_match.group().strip()
                                    break
                    except:
                        pass
                
                # Extract website
                website_selectors = [
                    'a[data-item-id^="authority:"]',
                    'a[data-item-id="authority"]',
                    '[data-tooltip="Open website"]',
                    'a[aria-label*="Website"]',
                    'a[data-item-id*="website"]'
                ]
                
                for selector in website_selectors:
                    try:
                        website_elem = await page.query_selector(selector)
                        if website_elem:
                            href = await website_elem.get_attribute('href')
                            if href:
                                # Google often wraps URLs - extract actual URL
                                if '/url?q=' in href:
                                    match = re.search(r'/url\?q=([^&]+)', href)
                                    if match:
                                        href = unquote(match.group(1))
                                # Skip Google domains
                                if not any(domain in href for domain in [
                                    'google.com', 'gstatic.com', 'googleapis.com', 
                                    'youtube.com', 'maps.google', 'google.co'
                                ]):
                                    result["website"] = href
                                    break
                    except:
                        continue
                
                # Extract rating
                try:
                    rating_elem = await page.query_selector('span[role="img"][aria-label*="star"]')
                    if rating_elem:
                        aria_label = await rating_elem.get_attribute('aria-label')
                        if aria_label:
                            rating_match = re.search(r'([\d.]+)\s*star', aria_label, re.IGNORECASE)
                            if rating_match:
                                result["rating"] = float(rating_match.group(1))
                except:
                    pass
                
                # Backup: try span with rating value
                if not result["rating"]:
                    try:
                        rating_spans = await page.query_selector_all('span.ceNzKf, span.Aq14fc, div.F7nice span')
                        for span in rating_spans:
                            text = await span.inner_text()
                            try:
                                rating = float(text.strip())
                                if 1 <= rating <= 5:
                                    result["rating"] = rating
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # Extract review count
                try:
                    reviews_elem = await page.query_selector('span[aria-label*="review"], button[aria-label*="review"]')
                    if reviews_elem:
                        aria_label = await reviews_elem.get_attribute('aria-label')
                        if aria_label:
                            reviews_match = re.search(r'([\d,]+)\s*review', aria_label, re.IGNORECASE)
                            if reviews_match:
                                result["reviews"] = int(reviews_match.group(1).replace(',', ''))
                except:
                    pass
                
                # Backup: look for review count in parentheses
                if not result["reviews"]:
                    try:
                        review_spans = await page.query_selector_all('span.UY7F9')
                        for span in review_spans:
                            text = await span.inner_text()
                            match = re.search(r'\(?([\d,]+)\)?', text)
                            if match:
                                count = int(match.group(1).replace(',', ''))
                                if count > 0:
                                    result["reviews"] = count
                                    break
                    except:
                        pass
                
                # Extract category
                try:
                    category_selectors = [
                        'button[jsaction*="category"]',
                        'span.DkEaL',
                        '[data-item-id="category"]'
                    ]
                    for selector in category_selectors:
                        cat_elem = await page.query_selector(selector)
                        if cat_elem:
                            cat_text = await cat_elem.inner_text()
                            if cat_text and len(cat_text) < 100:
                                result["category"] = cat_text.strip()
                                break
                except:
                    pass
                
                # Extract address
                try:
                    address_selectors = [
                        'button[data-item-id="address"]',
                        'button[aria-label*="Address"]',
                        '[data-item-id="address"]'
                    ]
                    for selector in address_selectors:
                        addr_elem = await page.query_selector(selector)
                        if addr_elem:
                            addr_text = await addr_elem.inner_text()
                            if addr_text and len(addr_text) < 200:
                                result["address"] = addr_text.strip()
                                break
                except:
                    pass
                
                logger.info(f"Extracted details: website={result['website']}, phone={result['phone']}, rating={result['rating']}, reviews={result['reviews']}")
                
            except Exception as e:
                logger.error(f"Error navigating to {maps_url}: {e}")
            
            await browser.close()
                
    except Exception as e:
        logger.error(f"Error fetching place details: {e}")
    
    return result
