import aiohttp
import asyncio
import logging
from typing import Optional, List
import os

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    logger.info("Telegram message sent successfully")
                    return True
                else:
                    error = await response.text()
                    logger.error(f"Telegram error: {error}")
                    return False
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

async def send_telegram_document(file_path: str, caption: str = "") -> bool:
    """Send a file/document to Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    
    try:
        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('chat_id', TELEGRAM_CHAT_ID)
                data.add_field('document', f, filename=os.path.basename(file_path))
                if caption:
                    data.add_field('caption', caption)
                
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        logger.info(f"Telegram document sent: {file_path}")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Telegram error: {error}")
                        return False
    except Exception as e:
        logger.error(f"Failed to send Telegram document: {e}")
        return False

def format_lead_message(lead: dict) -> str:
    """Format a lead for Telegram notification."""
    stars = "⭐" * int(lead.get('rating', 0)) if lead.get('rating') else ""
    
    msg = f"""🎯 <b>New Lead Found!</b>

📍 <b>{lead.get('name', 'Unknown')}</b>
{stars} {lead.get('rating', 'N/A')} ({lead.get('reviews', 0)} reviews)

📞 Phone: <code>{lead.get('phone', 'Not found')}</code>
🌐 Website: {lead.get('website') or 'No website ✅'}
📍 {lead.get('address', 'N/A')}

🏷️ Type: {lead.get('type', 'UNKNOWN')}
📊 Score: {lead.get('score', 0)}/10
"""
    
    if lead.get('demo_url'):
        msg += f"\n🖼️ Demo: {lead.get('demo_url')}"
    
    return msg

async def notify_high_value_lead(lead: dict, min_score: int = 5) -> bool:
    """Send notification for high-value leads (NO_WEBSITE type)."""
    if lead.get('score', 0) >= min_score or lead.get('type') == 'NO_WEBSITE':
        message = format_lead_message(lead)
        return await send_telegram_message(message)
    return False

async def send_daily_summary(stats: dict) -> bool:
    """Send daily summary to Telegram."""
    msg = f"""📊 <b>Daily Lead Summary</b>

📈 Total Leads: {stats.get('total', 0)}
📞 With Phone: {stats.get('with_phone', 0)}
🌐 Without Website: {stats.get('no_website', 0)} 🎯
⭐ High Score (5+): {stats.get('high_score', 0)}

🔝 <b>Top Leads Today:</b>
"""
    
    for i, lead in enumerate(stats.get('top_leads', [])[:5], 1):
        msg += f"\n{i}. {lead.get('name', 'Unknown')} - {lead.get('phone', 'No phone')}"
    
    return await send_telegram_message(msg)

async def export_leads_to_telegram(leads: List[dict], filename: str = "leads_export.csv") -> bool:
    """Export leads as CSV and send to Telegram."""
    import csv
    import tempfile
    
    # Create temp CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
        if leads:
            writer = csv.DictWriter(f, fieldnames=leads[0].keys())
            writer.writeheader()
            writer.writerows(leads)
        temp_path = f.name
    
    try:
        caption = f"📊 Lead Export - {len(leads)} leads"
        result = await send_telegram_document(temp_path, caption)
        return result
    finally:
        os.unlink(temp_path)
