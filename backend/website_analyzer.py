"""
Website analysis and lead scoring module.
Analyzes websites for SSL, mobile-friendliness, and calculates lead scores.
"""

import aiohttp
import time
import re
import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Configurable scoring from environment
NO_WEBSITE_SCORE = int(os.getenv("NO_WEBSITE_SCORE", "4"))
HIGH_RATING_SCORE = int(os.getenv("HIGH_RATING_SCORE", "2"))
HIGH_REVIEWS_SCORE = int(os.getenv("HIGH_REVIEWS_SCORE", "1"))
HAS_PHONE_SCORE = int(os.getenv("HAS_PHONE_SCORE", "1"))
HIGH_RATING_THRESHOLD = float(os.getenv("HIGH_RATING_THRESHOLD", "4.0"))
HIGH_REVIEWS_THRESHOLD = int(os.getenv("HIGH_REVIEWS_THRESHOLD", "20"))

# Request timeout
REQUEST_TIMEOUT = int(os.getenv("WEBSITE_CHECK_TIMEOUT", "15"))


async def analyze_website(url: str) -> dict:
    """
    Analyze a website for key metrics.
    
    Args:
        url: Website URL to analyze
        
    Returns:
        Dict with ssl_enabled, mobile_friendly, load_time
    """
    if not url:
        return {"ssl_enabled": False, "mobile_friendly": False, "load_time": 0.0}
    
    # Normalize URL
    url = normalize_url(url)
    ssl_enabled = url.startswith("https")
    start_time = time.time()
    
    try:
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, allow_redirects=True, ssl=False) as response:
                html = await response.text()
                load_time = time.time() - start_time
                
                # Check if redirected to HTTPS
                if response.url and str(response.url).startswith("https"):
                    ssl_enabled = True
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Check for mobile viewport meta tag
                viewport = soup.find('meta', attrs={'name': 'viewport'})
                mobile_friendly = viewport is not None
                
                # Additional mobile checks
                if not mobile_friendly:
                    # Check for responsive CSS or media queries
                    style_tags = soup.find_all('style')
                    for style in style_tags:
                        if style.string and '@media' in style.string:
                            mobile_friendly = True
                            break
                    
                    # Check for responsive meta tags
                    responsive_meta = soup.find('meta', attrs={'name': 'MobileOptimized'})
                    if responsive_meta:
                        mobile_friendly = True
                
                logger.info(f"Analyzed {url}: SSL={ssl_enabled}, Mobile={mobile_friendly}, Load={load_time:.2f}s")
                
                return {
                    "ssl_enabled": ssl_enabled,
                    "mobile_friendly": mobile_friendly,
                    "load_time": round(load_time, 2)
                }
                
    except aiohttp.ClientError as e:
        logger.warning(f"Connection error for {url}: {e}")
        return {"ssl_enabled": ssl_enabled, "mobile_friendly": False, "load_time": 99.9}
    except Exception as e:
        logger.error(f"Error analyzing {url}: {e}")
        return {"ssl_enabled": ssl_enabled, "mobile_friendly": False, "load_time": 99.9}


def normalize_url(url: str) -> str:
    """Normalize and clean URL."""
    url = url.strip()
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    
    # Parse and rebuild
    parsed = urlparse(url)
    
    # Remove trailing slash from path
    path = parsed.path.rstrip('/') if parsed.path != '/' else ''
    
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def validate_phone(phone: str) -> bool:
    """Validate phone number format."""
    if not phone:
        return False
    
    # Remove all non-digit characters except +
    digits = re.sub(r'[^\d+]', '', phone)
    
    # Should have at least 10 digits
    digit_count = len(re.sub(r'\D', '', digits))
    
    return digit_count >= 10


def calculate_lead_score(has_website: bool, rating: float, reviews: int, has_phone: bool) -> int:
    """
    Calculate lead score based on business attributes.
    
    Score breakdown:
    - No website: +4 points (highest priority for web dev services)
    - High rating (>4.0): +2 points (established business)
    - Good reviews (>20): +1 point (active business)
    - Has phone: +1 point (contactable)
    
    Max score: 8
    """
    score = 0
    
    if not has_website:
        score += NO_WEBSITE_SCORE
    
    if rating and rating > HIGH_RATING_THRESHOLD:
        score += HIGH_RATING_SCORE
    
    if reviews and reviews > HIGH_REVIEWS_THRESHOLD:
        score += HIGH_REVIEWS_SCORE
    
    if has_phone:
        score += HAS_PHONE_SCORE
    
    return min(score, 10)  # Cap at 10


def determine_lead_type(has_website: bool, mobile_friendly: bool) -> str:
    """
    Determine lead type based on website status.
    
    Types:
    - NO_WEBSITE: No website at all (highest priority)
    - WEBSITE_REDESIGN: Has website but not mobile-friendly (medium priority)
    - NORMAL: Has mobile-friendly website (lowest priority)
    """
    if not has_website:
        return "NO_WEBSITE"
    if not mobile_friendly:
        return "WEBSITE_REDESIGN"
    return "NORMAL"


def score_lead_detailed(business: dict) -> dict:
    """
    Get detailed scoring breakdown for a business.
    
    Args:
        business: Dict with website, rating, reviews, phone
        
    Returns:
        Dict with score, type, and breakdown
    """
    has_website = bool(business.get('website'))
    rating = business.get('rating')
    reviews = business.get('reviews')
    has_phone = bool(business.get('phone'))
    
    breakdown = {
        "no_website": 0,
        "high_rating": 0,
        "good_reviews": 0,
        "has_phone": 0
    }
    
    if not has_website:
        breakdown["no_website"] = NO_WEBSITE_SCORE
    if rating and rating > HIGH_RATING_THRESHOLD:
        breakdown["high_rating"] = HIGH_RATING_SCORE
    if reviews and reviews > HIGH_REVIEWS_THRESHOLD:
        breakdown["good_reviews"] = HIGH_REVIEWS_SCORE
    if has_phone:
        breakdown["has_phone"] = HAS_PHONE_SCORE
    
    total_score = sum(breakdown.values())
    lead_type = determine_lead_type(has_website, business.get('mobile_friendly', True))
    
    return {
        "score": min(total_score, 10),
        "type": lead_type,
        "breakdown": breakdown,
        "max_possible": NO_WEBSITE_SCORE + HIGH_RATING_SCORE + HIGH_REVIEWS_SCORE + HAS_PHONE_SCORE
    }

